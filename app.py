#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音短视频下载工具 - Windows 版本
无水印最高清晰度下载，支持博主主页批量下载
"""

import os
import re
import json
import sys
import time
import threading
import traceback
import urllib.request
import urllib.parse
import urllib.error
import subprocess
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
import logging

from flask import Flask, render_template, request, jsonify, send_from_directory, Response

# ============ 配置 ============
BASE_DIR = Path(__file__).parent.resolve()
LOG_FILE = BASE_DIR / "downloader.log"

# 配置日志
def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 文件日志
    file_handler = RotatingFileHandler(
        LOG_FILE, 
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # 同时输出到控制台
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(file_formatter)
    logger.addHandler(console_handler)
    
    return logger

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# ============ 配置 ============
BASE_DIR = Path(__file__).parent.resolve()
SETTINGS_FILE = BASE_DIR / "settings.json"
HISTORY_FILE = BASE_DIR / "download_history.json"
FAVORITES_FILE = BASE_DIR / "favorites.json"
COOKIE_FILE = BASE_DIR / "cookies.txt"

# 默认下载目录为程序目录下的 downloads
DEFAULT_DOWNLOAD_DIR = BASE_DIR / "downloads"
DEFAULT_DOWNLOAD_DIR.mkdir(exist_ok=True)


def load_settings():
    return load_json(SETTINGS_FILE, {})


def save_settings(settings):
    save_json(SETTINGS_FILE, settings)


def test_dir_write_permission(dir_path):
    """测试目录是否可写 - 使用最简单可靠的方法"""
    try:
        import os
        import random
        
        # 生成唯一的测试文件名
        test_name = "perm_test_{}_{}.tmp".format(os.getpid(), random.randint(10000, 99999))
        test_file = dir_path / test_name
        
        # 尝试创建文件
        try:
            with open(test_file, 'wb') as f:
                f.write(b'permission_test')
        except PermissionError:
            return False, "无法创建文件，权限被拒绝"
        except Exception as e:
            return False, "无法创建文件: {}".format(str(e))
        
        # 尝试删除文件
        try:
            os.unlink(test_file)
            return True, None
        except Exception as e:
            # 文件创建成功但删除失败，也算有权限
            # 尝试其他方式删除
            try:
                Path(test_file).unlink()
                return True, None
            except:
                return True, None  # 忽略删除失败
        
    except Exception as e:
        return False, "权限测试失败: {}".format(str(e))


def get_download_dir():
    """获取当前下载目录"""
    settings = load_settings()
    custom_dir = settings.get("download_dir", "")
    if custom_dir:
        p = Path(custom_dir)
        if p.exists() and p.is_dir():
            # 测试写入权限
            can_write, error_msg = test_dir_write_permission(p)
            if can_write:
                return p.resolve()
            else:
                logger.warning("Custom dir has no write permission: {}, error: {}".format(custom_dir, error_msg))
    # 返回默认目录
    DEFAULT_DOWNLOAD_DIR.mkdir(exist_ok=True)
    return DEFAULT_DOWNLOAD_DIR


# 下载状态
download_tasks = {}
lock = threading.Lock()

# 抖音 API
DOUYIN_AWEME_LIST_API = "https://www.douyin.com/aweme/v1/web/aweme/post/"
DOUYIN_AWEME_DETAIL_API = "https://www.douyin.com/aweme/v1/web/aweme/detail/"


def load_json(filepath, default=None):
    if default is None:
        default = {}
    if filepath.exists():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_history():
    return load_json(HISTORY_FILE, {})


def save_history(history):
    save_json(HISTORY_FILE, history)


def load_favorites():
    return load_json(FAVORITES_FILE, [])


def save_favorites(favs):
    save_json(FAVORITES_FILE, favs)


def get_downloaded_path(video_id):
    history = load_history()
    if video_id in history:
        path = history[video_id].get("local_path", "")
        if path and os.path.exists(path):
            return path
    return None


@app.route("/api/check_cookie", methods=["GET"])
def check_cookie():
    """检查Cookie文件是否存在"""
    return jsonify({"exists": COOKIE_FILE.exists() and COOKIE_FILE.stat().st_size > 0})


@app.route("/api/save_cookie", methods=["POST"])
def save_cookie():
    """保存Cookie到文件"""
    try:
        data = request.get_json()
        content = data.get("content", "").strip()
        if not content:
            return jsonify({"success": False, "message": "Cookie内容不能为空"})

        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            f.write(content)

        return jsonify({"success": True, "message": "Cookie保存成功"})
    except Exception as e:
        return jsonify({"success": False, "message": "保存失败: " + str(e)})


def load_cookies():
    if not COOKIE_FILE.exists():
        return ""
    try:
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return ""
        if content.startswith("["):
            cookies = {}
            for item in json.loads(content):
                name = item.get("name", "")
                value = item.get("value", "")
                if name:
                    cookies[name] = value
            return "; ".join("{}={}".format(k, v) for k, v in cookies.items())
        if content.startswith("#"):
            cookies = {}
            for line in content.split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("\t")
                if len(parts) >= 7:
                    cookies[parts[5].strip()] = parts[6].strip()
            return "; ".join("{}={}".format(k, v) for k, v in cookies.items())
        if "=" in content and not content.startswith("{"):
            return content
        return ""
    except Exception as e:
        logger.warning("Failed to load cookies: {}".format(e))
        return ""


def make_request(url, params=None, extra_headers=None):
    if params:
        url = "{}?{}".format(url, urllib.parse.urlencode(params))
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.douyin.com/",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    cookie_str = load_cookies()
    if cookie_str:
        headers["Cookie"] = cookie_str
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = resp.read().decode("utf-8", errors="replace")
        if not data.strip():
            logger.error("API returned empty data: {}".format(url))
            raise Exception("API 返回空数据，可能是未登录或被限制访问")
        try:
            return json.loads(data)
        except json.JSONDecodeError as je:
            logger.error("JSON parse failed - received: {}".format(data[:500]))
            logger.error("JSON error: {}".format(str(je)))
            raise Exception("API 返回了非 JSON 数据，可能是登录页面或被拦截。请设置 cookies.txt")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        logger.error("HTTP ERROR {} - {} - {}".format(e.code, url, body[:300]))
        raise Exception("HTTP 错误 {}: {}".format(e.code, body[:200] if body else "无响应体"))
    except Exception as e:
        if "JSON" not in str(e) and "空数据" not in str(e):
            logger.error("Request error: {} - {}".format(url, str(e)))
        raise


def resolve_share_url(share_url):
    if "douyin.com/user/" in share_url:
        return share_url
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    req = urllib.request.Request(share_url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return resp.geturl()
    except Exception:
        return share_url


def extract_sec_uid(url):
    m = re.search(r'/user/([A-Za-z0-9_-]+)', url)
    if m:
        return m.group(1)
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    if "sec_user_id" in params:
        return params["sec_user_id"][0]
    if "sec_uid" in params:
        return params["sec_uid"][0]
    return None


def extract_best_video_url(video_data):
    bit_rate_list = video_data.get("bit_rate", [])
    if bit_rate_list:
        best = sorted(bit_rate_list, key=lambda x: x.get("bit_rate", 0), reverse=True)[0]
        play_addr = best.get("play_addr", {})
        url_list = play_addr.get("url_list", [])
        if url_list:
            for u in url_list:
                if "playwm" not in u:
                    return u
            return url_list[0]
    play_addr = video_data.get("play_addr", {})
    url_list = play_addr.get("url_list", [])
    if url_list:
        for u in url_list:
            if "playwm" not in u:
                return u
        return url_list[0]
    download_addr = video_data.get("download_addr", {})
    url_list = download_addr.get("url_list", [])
    if url_list:
        return url_list[0]
    return None


def extract_play_url(video_data):
    """提取带水印的可播放地址（用于预览）"""
    play_addr = video_data.get("play_addr", {})
    url_list = play_addr.get("url_list", [])
    if url_list:
        for u in url_list:
            if "playwm" in u:
                return u
        return url_list[0]
    bit_rate_list = video_data.get("bit_rate", [])
    if bit_rate_list:
        best = sorted(bit_rate_list, key=lambda x: x.get("bit_rate", 0), reverse=True)[0]
        play_addr = best.get("play_addr", {})
        url_list = play_addr.get("url_list", [])
        if url_list:
            for u in url_list:
                if "playwm" in u:
                    return u
            return url_list[0]
    return None


def get_user_videos(profile_url):
    logger.info("Fetching user videos from: {}".format(profile_url))
    if "v.douyin.com" in profile_url:
        profile_url = resolve_share_url(profile_url)
    sec_uid = extract_sec_uid(profile_url)
    if not sec_uid:
        raise Exception("无法从链接中提取用户ID，请确认链接格式正确。\n正确格式: https://www.douyin.com/user/MS4wLjABAAAA...")

    all_videos = []
    cursor = 0
    for page in range(10):
        try:
            videos, has_more, next_cursor = get_user_videos_from_api(sec_uid, cursor=cursor)
        except Exception as e:
            if page == 0:
                raise
            break
        all_videos.extend(videos)
        if not has_more or not videos:
            break
        cursor = next_cursor
        time.sleep(0.5)
    logger.info("Total videos fetched: {}".format(len(all_videos)))
    return all_videos


def get_user_videos_from_api(url_or_sec_uid, cursor=0):
    """支持直接传入URL或sec_uid"""
    if "douyin.com" in url_or_sec_uid:
        if "v.douyin.com" in url_or_sec_uid:
            url_or_sec_uid = resolve_share_url(url_or_sec_uid)
        sec_uid = extract_sec_uid(url_or_sec_uid)
        if not sec_uid:
            raise Exception("无法从链接中提取用户ID")
    else:
        sec_uid = url_or_sec_uid
    
    params = {
        "sec_user_id": sec_uid,
        "count": 30,
        "max_cursor": cursor,
        "aid": "6383",
        "dytk": "",
        "device_platform": "webapp",
    }
    try:
        data = make_request(DOUYIN_AWEME_LIST_API, params=params)
    except Exception:
        try:
            data = make_request(DOUYIN_AWEME_LIST_API, params=params,
                              extra_headers={"Accept": "*/*"})
        except Exception as e2:
            raise Exception("API 请求失败: {}".format(str(e2)))

    if data.get("status_code") != 0:
        msg = data.get("status_msg", "未知错误")
        raise Exception("API 返回错误: {} (code: {})".format(msg, data.get("status_code")))

    aweme_list = data.get("aweme_list", [])
    has_more = data.get("has_more", 0) == 1
    next_cursor = data.get("max_cursor", 0)

    videos = []
    history = load_history()

    for item in aweme_list:
        try:
            aweme_id = str(item.get("aweme_id", item.get("id", "")))
            if not aweme_id:
                continue
            desc = item.get("desc", "") or "无标题"
            if len(desc) > 80:
                desc = desc[:80] + "..."
            video = item.get("video", {})
            cover = ""
            if video.get("cover") and video["cover"].get("url_list"):
                cover = video["cover"]["url_list"][0]
            if not cover and video.get("origin_cover") and video["origin_cover"].get("url_list"):
                cover = video["origin_cover"]["url_list"][0]
            duration = video.get("duration", 0)
            duration_str = "{:02d}:{:02d}".format(int(duration) // 1000 // 60, int(duration) // 1000 % 60) if duration else ""
            video_download_url = extract_best_video_url(video)
            video_play_url = extract_play_url(video)
            video_page_url = "https://www.douyin.com/video/{}".format(aweme_id)
            videos.append({
                "id": aweme_id,
                "title": desc,
                "thumbnail": cover,
                "url": video_page_url,
                "download_url": video_download_url or "",
                "play_url": video_play_url or "",
                "duration": duration_str,
                "downloaded": aweme_id in history,
                "download_time": history.get(aweme_id, {}).get("download_time", ""),
                "local_path": history.get(aweme_id, {}).get("local_path", ""),
            })
        except Exception as e:
            logger.warning("Failed to parse video item: {}".format(e))
            continue
    return videos, has_more, next_cursor


def get_video_detail(aweme_id):
    params = {"aweme_id": aweme_id, "aid": "6383", "dytk": "", "device_platform": "webapp"}
    try:
        data = make_request(DOUYIN_AWEME_DETAIL_API, params=params)
        if data.get("status_code") == 0:
            detail = data.get("aweme_detail", {})
            if detail:
                return extract_best_video_url(detail.get("video", {}))
    except Exception as e:
        logger.warning("Failed to get video detail: {}".format(e))
    return None


def download_file(url, filepath, task_id):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.douyin.com/",
    }
    cookie_str = load_cookies()
    if cookie_str:
        headers["Cookie"] = cookie_str
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
    except Exception:
        req2 = urllib.request.Request(url, headers={"User-Agent": headers["User-Agent"], "Referer": "https://www.douyin.com/"})
        resp = urllib.request.urlopen(req2, timeout=30)
    file_size = int(resp.headers.get("Content-Length", 0))
    downloaded = 0
    chunk_size = 1024 * 512
    with open(filepath, "wb") as f:
        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            progress = (downloaded / file_size) * 100 if file_size > 0 else 0
            with lock:
                download_tasks[task_id]["progress"] = progress
                if file_size > 0:
                    download_tasks[task_id]["message"] = "下载中... {:.1f}% ({:.1f}MB/{:.1f}MB)".format(
                        progress, downloaded / 1024 / 1024, file_size / 1024 / 1024)
                else:
                    download_tasks[task_id]["message"] = "下载中... {:.1f}MB".format(downloaded / 1024 / 1024)
    return downloaded


def download_video(video_id, video_title, download_url=None, video_page_url=None):
    task_id = "task_{}_{}".format(video_id, int(time.time()))
    with lock:
        download_tasks[task_id] = {"status": "downloading", "progress": 0, "message": "准备下载...", "video_id": video_id, "video_path": None}

    def _download():
        import shutil
        import random
        import os
        
        try:
            download_dir = get_download_dir()
            logger.info("Download dir: {}".format(download_dir))
            logger.info("Dir exists: {}".format(download_dir.exists()))
            logger.info("Dir is writable: checking...")

            if not download_dir.exists():
                logger.error("Directory not found: {}".format(download_dir))
                with lock:
                    download_tasks[task_id].update({"status": "error", "message": "下载目录不存在"})
                return

            # 测试目录是否可写
            can_write, write_error = test_dir_write_permission(download_dir)
            logger.info("Dir writable: {}, error: {}".format(can_write, write_error))
            
            if not can_write:
                with lock:
                    download_tasks[task_id].update({
                        "status": "error", 
                        "message": "无法写入目录！错误: {}".format(write_error)
                    })
                return

            # 清理标题中的非法字符
            safe_title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', video_title)[:100]
            if not safe_title or safe_title == '_':
                safe_title = 'video'
            
            # 生成唯一文件名，如果有重复则添加序号
            final_filepath = download_dir / "{}.mp4".format(safe_title)
            counter = 1
            while final_filepath.exists():
                final_filepath = download_dir / "{}_{}.mp4".format(safe_title, counter)
                counter += 1
            
            # 使用带随机后缀的临时文件到系统临时目录
            import tempfile
            system_temp = Path(tempfile.gettempdir())
            temp_suffix = random.randint(10000, 99999)
            temp_filepath = system_temp / "douyin_dl_{}_{}.mp4".format(video_id, temp_suffix)
            
            logger.info("Final path: {}".format(final_filepath))
            logger.info("Temp path (system): {}".format(temp_filepath))

            # 清理可能存在的临时文件
            if temp_filepath.exists():
                try:
                    temp_filepath.unlink()
                except:
                    pass

            url = download_url
            if not url and video_page_url:
                with lock:
                    download_tasks[task_id]["message"] = "获取视频地址..."
                url = get_video_detail(video_id)
            if not url:
                with lock:
                    download_tasks[task_id].update({"status": "error", "message": "无法获取视频下载地址"})
                return

            logger.info("Downloading: {}".format(video_title))
            
            # 下载到系统临时目录
            try:
                downloaded = download_file(url, str(temp_filepath), task_id)
                logger.info("Downloaded to temp, size: {} bytes".format(downloaded))
            except Exception as dl_err:
                logger.error("Download to temp failed: {}".format(dl_err))
                with lock:
                    download_tasks[task_id].update({
                        "status": "error", 
                        "message": "下载失败: {}".format(str(dl_err))
                    })
                return

            # 检查临时文件
            if not temp_filepath.exists() or temp_filepath.stat().st_size == 0:
                logger.error("Temp file invalid or empty")
                with lock:
                    download_tasks[task_id].update({"status": "error", "message": "下载失败，文件无效或为空"})
                return

            logger.info("Temp file size: {} bytes".format(temp_filepath.stat().st_size))

            # 将临时文件移动到目标目录
            try:
                shutil.move(str(temp_filepath), str(final_filepath))
                logger.info("Moved to final location successfully")
            except Exception as move_err:
                logger.warning("Move failed: {}, trying copy...".format(move_err))
                try:
                    shutil.copy2(str(temp_filepath), str(final_filepath))
                    temp_filepath.unlink()
                    logger.info("Copied to final location successfully")
                except Exception as copy_err:
                    logger.error("Copy also failed: {}, keeping temp file".format(copy_err))
                    # 使用临时文件作为最终文件
                    final_filepath = temp_filepath

            # 验证最终文件
            if final_filepath.exists() and final_filepath.stat().st_size > 0:
                logger.info("Final file verified, size: {} bytes".format(final_filepath.stat().st_size))
                with lock:
                    download_tasks[task_id].update({
                        "status": "completed", 
                        "progress": 100, 
                        "message": "下载完成！({:.1f}MB)".format(downloaded / 1024 / 1024), 
                        "video_path": str(final_filepath)
                    })
                history = load_history()
                history[video_id] = {
                    "title": video_title, 
                    "url": video_page_url or "", 
                    "local_path": str(final_filepath), 
                    "download_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                    "file_size": final_filepath.stat().st_size
                }
                save_history(history)
            else:
                logger.error("Final file verification failed")
                if final_filepath.exists():
                    try:
                        final_filepath.unlink()
                    except:
                        pass
                with lock:
                    download_tasks[task_id].update({"status": "error", "message": "下载失败，文件验证失败"})
                    
        except Exception as e:
            logger.error("Download exception: {}".format(traceback.format_exc()))
            with lock:
                download_tasks[task_id].update({"status": "error", "message": "下载失败: {}".format(str(e))})

    threading.Thread(target=_download, daemon=True).start()
    return task_id


# ============ 路由 ============

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/fetch_videos", methods=["POST"])
def fetch_videos():
    data = request.get_json()
    url = data.get("url", "").strip()
    cursor = data.get("cursor", 0)
    
    if not url:
        return jsonify({"success": False, "message": "请输入博主主页链接"})
    if "douyin.com" not in url:
        return jsonify({"success": False, "message": "请输入有效的抖音链接"})
    
    try:
        # 第一次请求获取基本信息
        if cursor == 0:
            videos, has_more, next_cursor = get_user_videos_from_api(url)
            if not videos:
                return jsonify({"success": False, "message": "未找到视频。可能原因:\n1. 链接格式不正确\n2. 需要设置 cookies.txt\n3. 该账号为私密账号"})
            return jsonify({
                "success": True, 
                "videos": videos, 
                "total": -1,  # -1表示未知总数
                "has_more": has_more, 
                "cursor": next_cursor,
                "downloaded_count": sum(1 for v in videos if v["downloaded"])
            })
        else:
            # 增量加载更多
            videos, has_more, next_cursor = get_user_videos_from_api(url, cursor=cursor)
            return jsonify({
                "success": True, 
                "videos": videos, 
                "has_more": has_more, 
                "cursor": next_cursor,
                "downloaded_count": sum(1 for v in videos if v["downloaded"])
            })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/api/download", methods=["POST"])
def download():
    data = request.get_json()
    videos = data.get("videos", [])
    if not videos:
        return jsonify({"success": False, "message": "请选择要下载的视频"})
    task_ids = []
    for video in videos:
        video_id = video["id"]
        video_title = video["title"]
        video_url = video.get("url", "")
        download_url = video.get("download_url", "")
        task_id = download_video(video_id, video_title, download_url=download_url, video_page_url=video_url)
        task_ids.append({"task_id": task_id, "video_id": video_id, "video_title": video_title})
    return jsonify({"success": True, "message": "已开始下载 {} 个视频".format(len(task_ids)), "tasks": task_ids})


@app.route("/api/download_status", methods=["POST"])
def download_status():
    data = request.get_json()
    task_ids = data.get("task_ids", [])
    statuses = {}
    with lock:
        for tid in task_ids:
            if tid in download_tasks:
                statuses[tid] = download_tasks[tid]
    return jsonify({"success": True, "statuses": statuses})


@app.route("/api/downloaded_file/<video_id>")
def get_downloaded_file(video_id):
    path = get_downloaded_path(video_id)
    if path and os.path.exists(path):
        return send_from_directory(os.path.dirname(path), os.path.basename(path), as_attachment=True)
    return jsonify({"success": False, "message": "文件不存在"}), 404


@app.route("/api/history")
def get_history():
    return jsonify({"success": True, "history": load_history()})


@app.route("/api/clear_history", methods=["POST"])
def clear_history():
    save_history({})
    return jsonify({"success": True, "message": "历史记录已清除"})


# ============ 收藏 API ============

@app.route("/api/favorites", methods=["GET"])
def get_favorites():
    return jsonify({"success": True, "favorites": load_favorites()})


@app.route("/api/favorites", methods=["POST"])
def add_favorite():
    data = request.get_json()
    url = data.get("url", "").strip()
    name = data.get("name", "").strip()
    if not url:
        return jsonify({"success": False, "message": "链接不能为空"})
    if not name:
        name = "博主"
    favs = load_favorites()
    for f in favs:
        if f.get("url") == url:
            return jsonify({"success": False, "message": "已收藏过该链接"})
    favs.append({"url": url, "name": name, "added_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    save_favorites(favs)
    return jsonify({"success": True, "message": "收藏成功"})


@app.route("/api/favorites/<int:index>", methods=["DELETE"])
def remove_favorite(index):
    favs = load_favorites()
    if 0 <= index < len(favs):
        removed = favs.pop(index)
        save_favorites(favs)
        return jsonify({"success": True, "message": "已取消收藏"})
    return jsonify({"success": False, "message": "收藏不存在"}), 404


@app.route("/api/settings", methods=["GET"])
def get_settings():
    settings = load_settings()
    download_dir = get_download_dir()
    can_write, error_msg = test_dir_write_permission(download_dir)
    return jsonify({
        "download_dir": settings.get("download_dir", ""),
        "current_dir": str(download_dir),
        "has_write_permission": can_write,
        "permission_error": error_msg if not can_write else None,
    })


@app.route("/api/settings", methods=["POST"])
def update_settings():
    data = request.get_json(force=True)
    settings = load_settings()
    if "download_dir" in data:
        dir_path = data["download_dir"].strip()
        if dir_path:
            p = Path(dir_path)
            if not p.exists():
                try:
                    p.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    return jsonify({"success": False, "message": "无法创建目录: {}".format(e)})
            
            # 检查目录是否有写入权限
            can_write, error_msg = test_dir_write_permission(p)
            if not can_write:
                return jsonify({
                    "success": False, 
                    "message": "该目录没有写入权限！\n\n可能原因：\n1. 目录在系统保护区域（如桌面、文档）\n2. 需要管理员权限\n3. 目录被其他程序占用\n\n建议：\n- 使用程序目录下的文件夹\n- 或创建一个新文件夹（如 D:\\MyVideos）"
                })
            
            settings["download_dir"] = dir_path
        else:
            settings.pop("download_dir", None)
    save_settings(settings)
    return jsonify({"success": True, "current_dir": str(get_download_dir())})


@app.route("/api/browse_folder", methods=["POST"])
def browse_folder():
    """打开Windows文件夹选择对话框"""
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        folder_path = filedialog.askdirectory(
            title="选择下载目录",
            initialdir=str(get_download_dir())
        )
        
        root.destroy()
        
        if folder_path:
            return jsonify({"success": True, "path": folder_path})
        else:
            return jsonify({"success": False, "message": "未选择目录"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/api/open_downloads", methods=["POST"])
def open_downloads():
    """在资源管理器中打开下载目录（Windows 版本）"""
    try:
        path = str(get_download_dir())
        if not os.path.exists(path):
            path = os.path.dirname(path)
        subprocess.Popen(f'explorer "{path}"')
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/downloads/<path:filename>")
def serve_download(filename):
    return send_from_directory(str(get_download_dir()), filename)


# 视频代理播放
_video_url_cache = {}


@app.route("/api/play/<video_id>")
def proxy_play(video_id):
    url = request.args.get("url", "")
    if not url:
        return jsonify({"error": "缺少视频地址"}), 400

    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        req.add_header("Referer", "https://www.douyin.com/")
        req.add_header("Accept", "*/*")

        response = urllib.request.urlopen(req, timeout=15)
        content_type = response.headers.get("Content-Type", "video/mp4")
        content_length = response.headers.get("Content-Length", "")

        def generate():
            while True:
                chunk = response.read(65536)
                if not chunk:
                    break
                yield chunk

        resp = Response(generate(), mimetype=content_type)
        if content_length:
            resp.headers["Content-Length"] = content_length
        resp.headers["Accept-Ranges"] = "bytes"
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp
    except Exception as e:
        logger.error("Video proxy play failed: {}".format(e))
        return jsonify({"error": str(e)}), 500


def open_browser():
    """启动后自动打开浏览器"""
    time.sleep(1.5)
    try:
        url = "http://127.0.0.1:5001"
        os.startfile(url)
    except Exception as e:
        logger.error("Failed to open browser: {}".format(e))


if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger()
    logger.info("=" * 50)
    logger.info("Douyin Downloader - Windows Version")
    logger.info("No watermark - HD Quality - Batch Download")
    logger.info("=" * 50)
    logger.info("Download dir: {}".format(get_download_dir()))
    logger.info("Open browser: http://127.0.0.1:5001")
    logger.info("Log file: {}".format(LOG_FILE))
    logger.info("=" * 50)
    
    # 启动浏览器
    threading.Thread(target=open_browser, daemon=True).start()
    
    # 启动Flask
    app.run(host="0.0.0.0", port=5001, debug=False)
