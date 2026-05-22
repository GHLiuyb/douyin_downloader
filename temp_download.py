    def _download():
        try:
            download_dir = get_download_dir()
            print("[INFO] 下载目录: {}".format(download_dir))

            if not download_dir.exists():
                print("[ERROR] 下载目录不存在: {}".format(download_dir))
                with lock:
                    download_tasks[task_id].update({"status": "error", "message": "下载目录不存在，请重新设置"})
                return

            def get_safe_path(counter=0):
                if counter == 0:
                    base_name = video_id
                else:
                    base_name = "{}_{}".format(video_id, counter)
                return download_dir / "{}.mp4".format(base_name)
            
            filepath = get_safe_path()
            counter = 0
            max_attempts = 10
            while filepath.exists() and counter < max_attempts:
                counter += 1
                filepath = get_safe_path(counter)
                
            print("[INFO] 文件路径: {}".format(filepath))

            url = download_url
            if not url and video_page_url:
                with lock:
                    download_tasks[task_id]["message"] = "获取视频地址..."
                url = get_video_detail(video_id)
            if not url:
                with lock:
                    download_tasks[task_id].update({"status": "error", "message": "无法获取视频下载地址"})
                return

            print("[INFO] 开始下载: {}".format(video_title))
            downloaded = download_file(url, str(filepath), task_id)

            if filepath.exists() and filepath.stat().st_size > 0:
                with lock:
                    download_tasks[task_id].update({"status": "completed", "progress": 100, "message": "下载完成！({:.1f}MB)".format(downloaded / 1024 / 1024), "video_path": str(filepath)})
                history = load_history()
                history[video_id] = {"title": video_title, "url": video_page_url or "", "local_path": str(filepath), "download_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "file_size": filepath.stat().st_size}
                save_history(history)
            else:
                if filepath.exists():
                    try:
                        filepath.unlink()
                    except:
                        pass
                with lock:
                    download_tasks[task_id].update({"status": "error", "message": "下载失败，文件为空"})
        except Exception as e:
            print("[ERROR] 下载异常: {}".format(traceback.format_exc()))
            with lock:
                download_tasks[task_id].update({"status": "error", "message": "下载失败: {}".format(str(e))})