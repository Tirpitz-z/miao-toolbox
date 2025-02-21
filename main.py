# coding: utf-8
import base64
import io
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
import cv2
import numpy as np
import pygetwindow as gw
import pyautogui
import pyperclip
import requests
import webview
from paddleocr import PaddleOCR
from data_processor import data_cleaning
import json
import keyboard
import pretty_midi
from PIL import Image


def load_config():
    config = {}
    with open('config', 'r', encoding='utf-8') as file:
        for line in file:
            if line.strip() and not line.startswith('#'):  # 跳过空行和注释
                key, value = line.strip().split('=')
                config[key.strip()] = int(value.strip())  # 将值转换为整数
    return config


def open_game_window():
    if len(gw.getWindowsWithTitle('ZhuxianClient')) == 0:
        print('未找到 ZhuxianClient 游戏窗口，请检查游戏是否已启动。')
        exit(1)
    window = gw.getWindowsWithTitle('ZhuxianClient')[0]
    window.activate()


def verify_trade_window_openness():
    pyautogui.press('f')
    time.sleep(2)
    screenshot, game_window_x, game_window_y, game_window_width, game_window_height = take_screenshot()
    screenshot = screenshot.crop((0, 0, 280, 140))
    config = load_config()
    list_x = config['game_list_x']
    list_y = config['game_list_y']
    list_width = config['game_list_width']
    list_height = config['game_list_height']
    pyautogui.moveTo(game_window_x + list_x + list_width, game_window_y + list_y + 40)

    screenshot.save('auction_house.png')
    if ocr_text('auction_house.png').find('交易行') != -1:
        print('交易行已打开')
        send_message('交易行已打开')
    else:
        print('交易行未打开')
        send_message('交易行未打开')
        exit(1)


def open_auction_house():
    pyautogui.press('f')
    time.sleep(2)


def take_screenshot():
    game_window = pyautogui.getWindowsWithTitle('ZhuxianClient')[0]
    game_window_x, game_window_y, game_window_width, game_window_height = game_window.left, game_window.top, game_window.width, game_window.height
    screenshot = pyautogui.screenshot(region=(game_window_x, game_window_y, game_window_width, game_window_height))
    screenshot.save('current_screen.png')
    return screenshot, game_window_x, game_window_y, game_window_width, game_window_height


def get_role_info():
    """
    获取角色名
    :return:
    """
    # 获取当前游戏截图
    screenshot, game_window_x, game_window_y, game_window_width, game_window_height = take_screenshot()
    config = load_config()

    role_x = config['game_role_x']
    role_y = config['game_role_y']
    role_width = config['game_role_width']
    role_height = config['game_role_height']
    role_screenshot = screenshot.crop((role_x, role_y, role_x + role_width, role_y + role_height))
    role_screenshot.save('role_name.png')  # 保存角色名截图

    # 识别角色名
    role_name = ocr_text('role_name.png')

    return role_name


def get_server_info():
    """
    获取服务器信息
    :return:
    """
    # 获取当前游戏截图
    screenshot, game_window_x, game_window_y, game_window_width, game_window_height = take_screenshot()
    config = load_config()

    server_x = config['game_server_x']
    server_y = config['game_server_y']
    server_width = config['game_server_width']
    server_height = config['game_server_height']
    server_screenshot = screenshot.crop((server_x, server_y, server_x + server_width, server_y + server_height))
    server_screenshot.save('server_name.png')

    server_name = ocr_text('server_name.png')

    return server_name


def ocr_text(image_path):
    """
    图像文字识别
    :param image_path:
    :return:
    """
    img_path = image_path
    # 执行 OCR 操作
    result = ocr.ocr(img_path, cls=True)

    # 直接输出识别的文字内容
    for idx in range(len(result)):
        res = result[idx]
        for line in res:
            print(line)
    text_results = ' '.join([res[1][0] for idx in range(len(result)) for res in result[idx]])
    send_message(f'OCR识别结果：{text_results}')
    return text_results


def get_auction_data():
    """
    获取拍卖行数据
    """
    # 获取当前游戏截图
    screenshot, game_window_x, game_window_y, game_window_width, game_window_height = take_screenshot()
    config = load_config()

    list_x = config['game_list_x']
    list_y = config['game_list_y']
    list_width = config['game_list_width']
    list_height = config['game_list_height']

    # 创建截图文件夹 'auction_data'
    if not os.path.exists('auction_data'):
        os.makedirs('auction_data')
    # 清空 'auction_data' 文件夹，准备下次截图
    clear_folder('auction_data')

    screenshot_counter = 0
    scroll_amount = -1200  # 调整此值以改变滚动速度和距离
    max_screenshots = 300  # 设置最大截图数量作为终止条件
    threshold = 1000  # 阈值，用于判断截图差异是否足够大
    last_screenshot = None  # 用于存储上一张截图
    saved_images = []  # 用于存储所有保存的图片路径

    while screenshot_counter < max_screenshots:
        if screenshot_counter != 0:
            pyautogui.scroll(-1300)
            time.sleep(0.5)
        # 获取当前游戏截图
        screenshot = take_screenshot()[0]
        item_screenshot = screenshot.crop((list_x, list_y, list_x + list_width, list_y + list_height))

        # 如果不是第一次截图，进行对比
        if last_screenshot and compare_screenshots(last_screenshot, item_screenshot, threshold):
            print("页面没有变化，停止截图...")
            send_message("判断页面没有变化...")
            break  # 页面没有变化，结束截图循环

        filename = f'auction_data_{screenshot_counter}.png'
        file_path = os.path.join('auction_data', filename)
        item_screenshot.save(file_path)
        print(f'Saved {filename}')
        send_message(f'正在截图： {filename}')
        # 将保存的图片路径加入列表
        saved_images.append(file_path)

        # 滚动屏幕
        pyautogui.scroll(scroll_amount)
        last_screenshot = item_screenshot
        screenshot_counter += 1

    print('滚动截图循环结束')
    send_message("已停止截图...")
    return saved_images


def ocr_auction_data(saved_images):
    all_text = ""
    for image_path in saved_images:
        print(f"正在识别图片: {image_path}")
        send_message(f"正在识别图片: {image_path}")
        text = ocr_text(image_path)
        all_text += text + "\n"
    print("OCR识别结果:")
    print(all_text)
    return all_text


def compare_screenshots(screenshot1, screenshot2, threshold=1000):
    """
    比较两张截图，若差异小于设定阈值，返回True，表示页面没有变化。
    """
    img1 = np.array(screenshot1)
    img2 = np.array(screenshot2)

    # 计算两张截图的绝对差异
    diff = cv2.absdiff(img1, img2)

    # 计算差异部分的非零像素数量
    non_zero_count = np.count_nonzero(diff)

    # 如果差异小于阈值，表示页面没有变化
    return non_zero_count < threshold


def clear_folder(folder_path):
    """
    清空文件夹中的所有文件。
    """
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
    print(f"文件夹 {folder_path} 已清空。")


def save_cleaned_data(data, current_time):
    if not os.path.exists('cleaned_data'):
        os.makedirs('cleaned_data')
    filename = f'cleaned_data_{current_time}.csv'
    file_path = os.path.join('cleaned_data', filename)
    data.to_csv(file_path, index=False)


def monitor_mouse_move(stop_event):
    last_pos = pyautogui.position()
    while not stop_event.is_set():
        current_pos = pyautogui.position()
        if current_pos != last_pos:
            stop_event.set()
        time.sleep(0.1)


def send_message(message):
    js_code = f"window.postMessage({{ type: 'console', message: '{message}' }});"
    miaomiao_window.evaluate_js(js_code)


def upload_csv(file):
    try:
        file_path = os.path.join('cleaned_data', f'cleaned_data_{file}.csv')
        with open(file_path, 'rb') as f:
            files = {'file': (f'cleaned_data_{file}.csv', f, 'text/csv')}
            response = requests.post('http://47.109.79.138:5000/upload_csv', files=files)

        if response.status_code == 200:
            send_message(f"文件上传成功: {response.json()['message']}")
            print(f"文件上传成功: {response.json()['message']}")
        else:
            send_message(f"文件上传失败: {response.text}")
            print(f"文件上传失败: {response.text}")
    except Exception as upload_error:
        send_message(f"上传出现错误: {upload_error}")
        print(f"上传出现错误: {upload_error}")


MIDI_MAP = {
    36: 'a', 38: 's', 40: 'd', 41: 'f', 43: 'g', 45: 'h', 47: 'j',  # C3 to B3
    48: 'q', 50: 'w', 52: 'e', 53: 'r', 55: 't', 57: 'y', 59: 'u',  # C4 to B4
    60: '1', 62: '2', 64: '3', 65: '4', 67: '5', 69: '6', 71: '7',  # C5 to B5
}


def get_list_format(midi_file, speed):
    midi_data = pretty_midi.PrettyMIDI(midi_file)
    try:
        notes = midi_data.instruments[0].notes
    except IndexError:
        return []
    notes.sort(key=lambda x: x.start)
    play_list = []
    i = 0
    while i < len(notes):
        cur_time = notes[i].start
        note_list_temp = []
        while i < len(notes) and notes[i].start == cur_time:
            note_list_temp.append(notes[i])
            i += 1
        key_list = [MIDI_MAP.get(note.pitch, None) for note in note_list_temp]
        key_list = [key for key in key_list if key is not None]
        wait_time = notes[i].start - cur_time if i < len(notes) else 1
        wait_time /= speed
        play_list.append({'key_list': key_list, 'wait_time': wait_time})
    return play_list

def get_auction_data_custom():
    # 获取当前游戏截图
    screenshot, game_window_x, game_window_y, game_window_width, game_window_height = take_screenshot()
    config = load_config()

    list_x = config['game_list_x']
    list_y = config['game_list_y']
    list_width = config['game_list_width']
    list_height = config['game_list_height']

    game_search_x = config['game_search_x']
    game_search_y = config['game_search_y']

    # 鼠标移动到搜索框
    pyautogui.moveTo(game_window_x + game_search_x, game_window_y + game_search_y)
    pyautogui.click()  # 点击使搜索框获得焦点

    # 加载自定义物品列表
    items = load_items_from_file('custom_items.txt')

    # 创建截图文件夹 'auction_data'
    if not os.path.exists('auction_data_custom'):
        os.makedirs('auction_data_custom')
    # 清空 'auction_data' 文件夹，准备下次截图
    clear_folder('auction_data_custom')

    screenshot_counter = 0
    saved_images = []  # 用于存储所有保存的图片路径

    for item in items:
        print(item)
        clear_search_box()
        time.sleep(0.5)  # 等待一段时间确保准备就绪
        write_with_delay(item)
        time.sleep(1)  # 等待搜索结果展示

        # 获取当前游戏截图
        screenshot = take_screenshot()[0]
        item_screenshot = screenshot.crop((list_x, list_y, list_x + list_width, list_y + list_height))
        filename = f'auction_data_custom_{screenshot_counter}.png'
        file_path = os.path.join('auction_data_custom', filename)
        item_screenshot.save(file_path)
        print(f'Saved {filename}')

        saved_images.append(file_path)
        screenshot_counter += 1

    print('滚动截图循环结束')
    return saved_images


def load_items_from_file(file_path):
    """从指定路径加载物品列表"""
    with open(file_path, 'r', encoding='utf-8') as file:
        items = [line.strip() for line in file.readlines()]
    return items


def clear_search_box():
    """模拟键盘操作清空搜索框"""
    pyautogui.click()  # 确保焦点在搜索框内
    pyautogui.hotkey('ctrl', 'a')  # 全选
    time.sleep(0.1)
    pyautogui.press('backspace')  # 删除


def write_with_delay(text):
    """处理包含非ASCII字符的文本输入"""
    pyperclip.copy(text)  # 将文本放入剪贴板
    pyautogui.hotkey('ctrl', 'v')  # 使用快捷键粘贴
    time.sleep(0.1)
    pyautogui.press('enter')
class GameAutomationAPI:
    def auto_upload(self):
        global ocr
        ocr = PaddleOCR(use_angle_cls=True, lang='ch')  # 初始化 PaddleOCR，设置为中文模式
        open_game_window()
        verify_trade_window_openness()
        pyautogui.press('esc')
        time.sleep(2)

        stop_event = threading.Event()
        mouse_thread = threading.Thread(target=monitor_mouse_move, args=(stop_event,))
        mouse_thread.start()
        try:
            if stop_event.is_set():
                gw_window = gw.getWindowsWithTitle('妙妙工具箱')[0]
                gw_window.activate()
                raise Exception("检测到鼠标移动，已中断上传。")

            server_info = get_server_info()
            send_message(f"当前服务器: {server_info}")

            if stop_event.is_set():
                gw_window = gw.getWindowsWithTitle('妙妙工具箱')[0]
                gw_window.activate()
                raise Exception("检测到鼠标移动，已中断上传。")

            pyautogui.press('f')
            time.sleep(2)
            if stop_event.is_set():
                gw_window = gw.getWindowsWithTitle('妙妙工具箱')[0]
                gw_window.activate()
                raise Exception("检测到鼠标移动，已中断上传。")

            saved_images = get_auction_data()
            gw_window = gw.getWindowsWithTitle('妙妙工具箱')[0]
            gw_window.activate()
            auction_data = ocr_auction_data(saved_images)
            send_message("OCR识别完成...")
            send_message("正在清洗数据...")
            current_time = datetime.now().strftime("%Y%m%d%H%M%S")
            df = data_cleaning(auction_data, server_info, current_time)
            save_cleaned_data(df, current_time)
            send_message(f"数据清洗完成，保存在 cleaned_data/{current_time}.csv")
            upload_csv(current_time)

        except Exception as e:
            print(f"出现错误: {e}")
            send_message(f"{e}")
        finally:
            stop_event.set()
            mouse_thread.join()

    def __init__(self):
        self.paused = False
        self.playing = False
        self.current_thread = None
        self.focus_check_thread = None
        self.stop_play_event = False
        self.stop_check_event = False
        self.file_path = os.path.dirname(os.path.abspath(__file__))

    def get_file_list(self, directory):
        try:
            files = os.listdir(directory)
            return json.dumps(files)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def toggle_pause(self, pause):
        """控制暂停与恢复"""
        self.paused = pause
        # print(f"Pause status: {self.paused}")
        status = {'isPaused': self.paused}
        miaomiao_window.evaluate_js(f'handlePlaybackStatus({json.dumps(status)})')

    def stop_current_playback(self):
        if self.current_thread and self.current_thread.is_alive():
            print("Stopping current playback...")
            self.stop_play_event = True
            self.current_thread.join()

    def stop_check_focus(self):
        if self.focus_check_thread and self.focus_check_thread.is_alive():
            print("Stopping focus check thread...")
            self.stop_check_event = True
            self.focus_check_thread.join()

    def play_audio(self, file, speed):
        if len(gw.getWindowsWithTitle('ZhuxianClient')) == 0:
            print('未找到 ZhuxianClient 游戏窗口，请检查游戏是否已启动。')
            exit(1)
        window = gw.getWindowsWithTitle('ZhuxianClient')[0]
        window.activate()

        speed = float(speed)
        directory = 'MIDI'
        file_path = os.path.join(directory, file)

        self.stop_current_playback()
        self.stop_play_event = False
        self.stop_check_focus()
        self.stop_check_event = False
        self.current_thread = threading.Thread(target=self._play_audio_thread, args=(file_path, speed))
        self.current_thread.start()
        self.focus_check_thread = threading.Thread(target=self._check_window_focus)
        self.focus_check_thread.start()

    def _play_audio_thread(self, file_path, speed):
        play_list = get_list_format(file_path, speed)
        self.playing = True

        for item in play_list:
            if self.stop_play_event:
                break

            key_list = item['key_list']
            wait_time = item['wait_time']

            for key in key_list:
                keyboard.press(key)
                print(f"Pressing {key}")

            time.sleep(wait_time)
            for key in key_list:
                keyboard.release(key)
                print(f"Releasing {key}")

            while self.paused:
                time.sleep(0.1)

    def pauseAudio(self):
        if self.paused:
            open_game_window()
            self.toggle_pause(False)
        else:
            self.toggle_pause(True)

    def _check_window_focus(self):
        while not self.stop_check_event:
            try:
                focused_window = gw.getActiveWindow()
                if focused_window:
                    window_title = focused_window.title.strip()
                    if window_title != 'ZhuxianClient':
                        if not self.paused:
                            print(f"焦点窗口不是 'ZhuxianClient'，暂停播放。")
                            self.toggle_pause(True)
                else:
                    print("没有活动窗口。")
            except Exception as e:
                print(f"检查窗口焦点时发生错误: {e}")
            time.sleep(0.5)

    def process_image(self, image_base64, x_size, threshold, x_offset, y_offset):
        image_data = base64.b64decode(image_base64)
        image_path = io.BytesIO(image_data)
        img = Image.open(image_path).convert('L')

        img = img.point(lambda x: 0 if x < threshold else 255, '1')

        y_size = round(x_size * 37 / 50)
        ratio = round(1312 / x_size)
        target_size = (x_size, y_size)
        print(target_size, ratio)

        img = img.resize(target_size)
        img.save("processed_image.png")
        with open("processed_image.png", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

        black_pixels = []
        white_pixels = []

        pixels = img.load()

        for y in range(img.height):
            for x in range(img.width):
                if pixels[x, y] == 0:  # 黑色
                    black_pixels.append({"PositionX": x, "PositionY": y})
                else:  # 白色
                    white_pixels.append({"PositionX": x, "PositionY": y})

        if len(black_pixels) < len(white_pixels):
            pixel_type = "black"
            pixel_num = len(black_pixels)
            save_data = {"ModuleData": [],
                         "PasterData": [
                             {"FlipType": 0, "PasterId": 137115, "PositionX": px["PositionX"] * ratio + x_offset,
                              "PositionY": px["PositionY"] * ratio + y_offset} for px in
                             black_pixels],
                         "Version": 1
                         }
        else:
            pixel_type = "white"
            pixel_num = len(white_pixels)
            save_data = {"ModuleData": [],
                         "PasterData": [
                             {"FlipType": 0, "PasterId": 137115, "PositionX": px["PositionX"] * ratio + x_offset,
                              "PositionY": px["PositionY"] * ratio + y_offset} for px in
                             white_pixels],
                         "Version": 1
                         }

        json_str = json.dumps(save_data, indent="\t", ensure_ascii=False)
        json_bytes = json_str.encode('utf-8')

        footer = b'\x00'
        file_size = len(json_bytes) + 1
        header = file_size.to_bytes(4, byteorder='little')

        data_with_metadata = header + json_bytes + footer
        base64_data = base64.b64encode(data_with_metadata).decode('utf-8')

        # print("Base64 编码后的数据：")
        # print(base64_data)

        with open('妙妙主页蓝图.info', 'w', encoding='utf-8') as f:
            f.write(base64_data)

        return json.dumps({'encoded_string': encoded_string, 'pixel_type': pixel_type, 'pixel_num': pixel_num})

    def open_folder(self):
        """打开文件所在的文件夹"""
        if sys.platform == "win32":
            subprocess.run(f'explorer "{self.file_path}"')
        elif sys.platform == "darwin":
            subprocess.run(["open", self.file_path])
        else:
            subprocess.run(["xdg-open", self.file_path])

    def custom_upload(self):
        global ocr
        ocr = PaddleOCR(use_angle_cls=True, lang='ch')
        open_game_window()
        verify_trade_window_openness()
        pyautogui.click()
        pyautogui.press('esc')
        time.sleep(2)
        saved_images = []
        server_info = get_server_info()
        pyautogui.press('f')
        time.sleep(2)
        saved_images = get_auction_data_custom()
        gw_window = gw.getWindowsWithTitle('妙妙工具箱')[0]
        gw_window.activate()
        auction_data_custom = ocr_auction_data(saved_images)
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
        df = data_cleaning(auction_data_custom, server_info, current_time)
        save_cleaned_data(df, current_time)
        # 上传
        upload_csv(current_time)

    def open_with_default_editor(self, file_name='custom_items.txt'):
        if not os.path.exists(file_name):
            raise FileNotFoundError(f"文件 {file_name} 未找到，请检查文件名是否正确以及文件是否存在于当前目录下。")

        try:
            # 根据操作系统选择合适的方法打开文件
            if os.name == 'nt':  # Windows
                os.startfile(file_name)
            elif os.name == 'posix':  # macOS, Linux
                subprocess.call(['open', file_name])
            else:
                subprocess.call(['xdg-open', file_name])
        except Exception as e:
            send_message("打开失败，请手动修改当前目录下的custom_items.txt文件")
            print(f"无法打开文件 {file_name}: {e}")


if __name__ == '__main__':
    game_api = GameAutomationAPI()
    miaomiao_window = webview.create_window("妙妙工具箱",
                                            "templates/index.html",
                                            js_api=game_api,
                                            width=888,
                                            height=666,
                                            )
    keyboard.add_hotkey('alt+.', game_api.pauseAudio)
    webview.start()

