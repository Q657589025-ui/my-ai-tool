import time
import json
import threading
from core.api_client import AIGCClient
from core.database import get_db_session, Task, Work
from core.auth import get_user_points, update_user_points
from core.utils import download_image
from config.price_map import PRICE_MAP
from datetime import datetime

def get_cost(task_type, params):
    if task_type == "image":
        return PRICE_MAP["image"]
    elif task_type == "video":
        quality = params.get("quality", "720p")
        return PRICE_MAP.get(f"video_{quality}", PRICE_MAP.get("video_720p", 100))
    elif task_type == "music":
        return PRICE_MAP["music"]
    elif task_type == "human":
        return PRICE_MAP["human"]
    elif task_type == "chat":
        return PRICE_MAP["chat"]
    return 10

class TaskWorker:
    def __init__(self):
        self.client = AIGCClient()

    def poll_task(self, task_id, user_id):
        db = get_db_session()
        try:
            db.query(Task).filter(Task.task_id == task_id).update({"status": "processing", "progress": 10})
            db.commit()
        finally:
            db.close()

        start = time.time()
        while time.time() - start < 150:
            status_resp = self.client.query_task(task_id)
            if "error" in status_resp:
                db = get_db_session()
                try:
                    db.query(Task).filter(Task.task_id == task_id).update({"status": "failed"})
                    db.commit()
                finally:
                    db.close()
                break

            status = status_resp.get("status")
            if status == "processing":
                db = get_db_session()
                try:
                    db.query(Task).filter(Task.task_id == task_id).update({"progress": 50})
                    db.commit()
                finally:
                    db.close()
            elif status in ["completed", "success"]:
                result = status_resp.get("result", {})
                cost = status_resp.get("usage", {}).get("points_cost", 0)
                db = get_db_session()
                try:
                    task = db.query(Task).filter(Task.task_id == task_id).first()
                    if task:
                        task.status = "completed"
                        task.progress = 100
                        task.result = json.dumps(result)
                        task.cost = cost
                        url = None
                        if "images" in result and result["images"]:
                            url = result["images"][0].get("url")
                        elif "video_url" in result:
                            url = result["video_url"]
                        elif "audio_url" in result:
                            url = result["audio_url"]
                        if url:
                            local_path = download_image(url) if "images" in result else url
                            work = Work(
                                user_id=user_id,
                                type=task.type,
                                title=task.prompt[:20],
                                prompt=task.prompt,
                                model=task.model,
                                url=local_path or url,
                                created_at=datetime.utcnow()
                            )
                            db.add(work)
                        db.commit()
                finally:
                    db.close()
                break
            elif status in ["failed", "cancelled"]:
                db = get_db_session()
                try:
                    db.query(Task).filter(Task.task_id == task_id).update({"status": "failed"})
                    db.commit()
                finally:
                    db.close()
                break
            time.sleep(2)
        else:
            db = get_db_session()
            try:
                db.query(Task).filter(Task.task_id == task_id).update({"status": "timeout"})
                db.commit()
            finally:
                db.close()

worker = TaskWorker()

def submit_task(user_id, task_type, model, channel, prompt, file, **params):
    if get_user_points(user_id) < get_cost(task_type, params):
        return None, "余额不足"

    client = AIGCClient()

    if task_type == "chat":
        messages = [{"role": "user", "content": prompt}]
        resp = client.chat_completion(model, channel, messages, **params)
        if "error" in resp:
            return None, resp["error"]

        if update_user_points(user_id, -get_cost(task_type, params)):
            choices = resp.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "")
                db = get_db_session()
                try:
                    work = Work(
                        user_id=user_id,
                        type="chat",
                        title=prompt[:20],
                        prompt=prompt,
                        model=model,
                        url=content,
                        created_at=datetime.utcnow()
                    )
                    db.add(work)
                    db.commit()
                finally:
                    db.close()
            return resp, None
        else:
            return None, "扣费失败"

    else:
        if file:
            from core.utils import file_to_data_uri
            uri = file_to_data_uri(file)
            if uri:
                params["image_urls"] = [uri]

        params["prompt"] = prompt
        resp = client.create_task(model, channel, **params)
        if "error" in resp:
            return None, resp["error"]

        task_id = resp.get("task_id")
        if not task_id:
            return None, "未返回 task_id"

        db = get_db_session()
        try:
            task = Task(
                task_id=task_id,
                user_id=user_id,
                type=task_type,
                model=model,
                prompt=prompt,
                status="waiting",
                progress=0,
                created_at=datetime.utcnow()
            )
            db.add(task)
            db.commit()
        finally:
            db.close()

        if update_user_points(user_id, -get_cost(task_type, params)):
            threading.Thread(target=worker.poll_task, args=(task_id, user_id), daemon=True).start()
            return {"task_id": task_id, "cost": get_cost(task_type, params)}, None
        else:
            return None, "扣费失败"
