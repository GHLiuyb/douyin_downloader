# API 接口文档

## 基础信息

- **Base URL**: `http://127.0.0.1:5001`
- **Content-Type**: `application/json`

---

## 视频相关接口

### 1. 获取视频列表

**接口**: `POST /api/fetch_videos`

**请求参数**:
```json
{
  "url": "https://www.douyin.com/user/MS4wLjABAAAA..."
}
```

**成功响应**:
```json
{
  "success": true,
  "videos": [
    {
      "id": "1234567890",
      "title": "视频标题",
      "thumbnail": "https://...",
      "url": "https://www.douyin.com/video/1234567890",
      "download_url": "https://v26-dy.ixigua.com/...",
      "play_url": "https://v26-dy.ixigua.com/...playwm...",
      "duration": "01:23",
      "downloaded": false,
      "download_time": "",
      "local_path": ""
    }
  ],
  "total": 61,
  "downloaded_count": 5,
  "nickname": ""
}
```

**失败响应**:
```json
{
  "success": false,
  "message": "错误信息"
}
```

---

### 2. 开始下载

**接口**: `POST /api/download`

**请求参数**:
```json
{
  "videos": [
    {
      "id": "1234567890",
      "title": "视频标题",
      "url": "https://www.douyin.com/video/1234567890",
      "download_url": "https://v26-dy.ixigua.com/..."
    }
  ]
}
```

**响应**:
```json
{
  "success": true,
  "message": "已开始下载 3 个视频",
  "tasks": [
    {
      "task_id": "task_1234567890_1699123456",
      "video_id": "1234567890",
      "video_title": "视频标题"
    }
  ]
}
```

---

### 3. 查询下载状态

**接口**: `POST /api/download_status`

**请求参数**:
```json
{
  "task_ids": ["task_1234567890_1699123456"]
}
```

**响应**:
```json
{
  "success": true,
  "statuses": {
    "task_1234567890_1699123456": {
      "status": "downloading",  // downloading/completed/error
      "progress": 45.5,
      "message": "下载中... 45.5% (2.5MB/5.5MB)",
      "video_id": "1234567890",
      "video_path": null
    }
  }
}
```

---

### 4. 下载已完成文件

**接口**: `GET /api/downloaded_file/<video_id>`

**响应**: 文件流（直接下载）

---

### 5. 视频代理播放

**接口**: `GET /api/play/<video_id>?url=<视频URL>`

**说明**: 用于解决抖音视频的 Referer 限制，通过后端代理播放

---

## 历史记录接口

### 6. 获取下载历史

**接口**: `GET /api/history`

**响应**:
```json
{
  "success": true,
  "history": {
    "1234567890": {
      "title": "视频标题",
      "url": "https://www.douyin.com/video/1234567890",
      "local_path": "C:\\Users\\...\\视频标题_1234567890.mp4",
      "download_time": "2024-01-15 10:30:00",
      "file_size": 12345678
    }
  }
}
```

---

### 7. 清除历史

**接口**: `POST /api/clear_history`

**响应**:
```json
{
  "success": true,
  "message": "历史记录已清除"
}
```

---

## 收藏接口

### 8. 获取收藏列表

**接口**: `GET /api/favorites`

**响应**:
```json
{
  "success": true,
  "favorites": [
    {
      "url": "https://www.douyin.com/user/...",
      "name": "博主昵称",
      "added_time": "2024-01-15 10:30:00"
    }
  ]
}
```

---

### 9. 添加收藏

**接口**: `POST /api/favorites`

**请求参数**:
```json
{
  "url": "https://www.douyin.com/user/...",
  "name": "博主昵称"
}
```

**响应**:
```json
{
  "success": true,
  "message": "收藏成功"
}
```

---

### 10. 删除收藏

**接口**: `DELETE /api/favorites/<index>`

**响应**:
```json
{
  "success": true,
  "message": "已取消收藏"
}
```

---

## 设置接口

### 11. 获取设置

**接口**: `GET /api/settings`

**响应**:
```json
{
  "download_dir": "D:\\Downloads\\抖音视频",
  "current_dir": "D:\\Downloads\\抖音视频"
}
```

---

### 12. 更新设置

**接口**: `POST /api/settings`

**请求参数**:
```json
{
  "download_dir": "D:\\Downloads\\抖音视频"
}
```

**响应**:
```json
{
  "success": true,
  "current_dir": "D:\\Downloads\\抖音视频"
}
```

**说明**: 传入空字符串 `""` 恢复默认目录

---

## 工具接口

### 13. 打开下载目录

**接口**: `POST /api/open_downloads`

**说明**: 在资源管理器中打开当前下载目录

**响应**:
```json
{
  "success": true
}
```

---

## 静态文件服务

### 14. 下载文件访问

**接口**: `GET /downloads/<filename>`

**说明**: 用于访问已下载的视频文件

---

## 错误码说明

| 状态 | 说明 |
|------|------|
| 200 | 成功 |
| 404 | 接口不存在或资源未找到 |
| 500 | 服务器内部错误 |

## 常见错误信息

- `请输入博主主页链接` - URL 为空
- `请输入有效的抖音链接` - URL 不包含 douyin.com
- `无法从链接中提取用户ID` - URL 格式不正确
- `API 请求失败` - 网络问题或需要 Cookie
- `无法获取视频下载地址` - 视频可能被删除或需要登录
