#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成简约大气的抖音下载器图标
需要安装 Pillow: pip install pillow
"""

import os
from PIL import Image, ImageDraw, ImageFont

def create_icon():
    sizes = [256, 128, 64, 48, 32, 16]
    images = []
    
    for size in sizes:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        center = size // 2
        radius = int(size * 0.42)
        
        # 极简背景 - 纯抖音色 (FE2C55)
        bg_color = (254, 44, 85, 255)  # 抖音官方品牌色
        draw.ellipse([center - radius, center - radius, center + radius, center + radius], fill=bg_color)
        
        # 绘制简约的下载箭头 (↓)
        arrow_size = int(size * 0.35)
        arrow_color = (255, 255, 255, 255)
        
        # 箭头位置居中
        arrow_x = center
        arrow_y = center
        
        # 箭头竖线
        line_width = max(3, size // 10)
        draw.rectangle([
            arrow_x - line_width // 2, 
            arrow_y - arrow_size // 2, 
            arrow_x + line_width // 2, 
            arrow_y + arrow_size // 4
        ], fill=arrow_color)
        
        # 箭头三角
        arrow_points = [
            (arrow_x - arrow_size // 2 - line_width, arrow_y - arrow_size // 6),
            (arrow_x + arrow_size // 2 + line_width, arrow_y - arrow_size // 6),
            (arrow_x, arrow_y + arrow_size // 2)
        ]
        draw.polygon(arrow_points, fill=arrow_color)
        
        images.append(img)
    
    # 保存为 ICO 文件
    images[0].save('icon.ico', format='ICO', sizes=[(s, s) for s in sizes])
    print('Icon created: icon.ico')
    
    # 同时保存一个 PNG 预览
    images[0].save('icon.png', format='PNG')
    print('Preview saved: icon.png')

if __name__ == '__main__':
    create_icon()
