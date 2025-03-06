import os
import re
import pandas as pd


class DataProcessor:
    @staticmethod
    def _extract_records(raw_data):
        pattern = r"([a-zA-Z\u4e00-\u9fa5·：:“”（）()]+)\s+(凡品|良品|珍品|灵品|仙品)\s+(\d{1,2})?\s*(\d+)?\s*(\d+(\.\d+)?(万|亿)?)?"
        return re.findall(pattern, raw_data)

    @staticmethod
    def _clean_price(salary_str):
        salary_str = salary_str.replace(" ", "")
        if '万' in salary_str:
            salary_str = salary_str.replace('万', '')
            return round(float(salary_str) * 10000)
        elif '亿' in salary_str:
            salary_str = salary_str.replace('亿', '')
            return round(float(salary_str) * 100000000)  # 将'万'替换成对应的数值
        try:
            if round(float(salary_str)) == 0:
                return
            return round(float(salary_str))
        except ValueError:
            raise ValueError(f"无法解析的价格字符串: {salary_str}")

    @staticmethod
    def extract_server_name(server_info):
        server_names = [
            "一剑诛仙",
            "风华绝代",
            "世外桃源",
            "瑶光沁雪",
            "浮生若梦",
            "风灵月影",
            "君临天下",
            "唯我独尊",
            "明月天涯",
            "天下无双",
            "九霄龙吟",
            "情撼九天",
            "绮梦天华",
            "龙渊墨雪",
            "六道轮回",
            "紫电青霜",
            "三界凡尘",
            "金风玉露",
            "幻月御风"]
        for name in server_names:
            match_count = 0
            for char in name:
                if char in server_info:
                    match_count += 1
                if match_count >= len(name) - 1:
                    return name
        return None

    def _process_matches(self, matches):
        cleaned_data = []
        for match in matches:
            name = match[0]
            quality = match[1]
            level = match[2] if match[2] else None
            quantity = match[3] if match[3] else None
            price = self._clean_price(match[4]) if match[4] else None
            cleaned_data.append([name, quality, level, quantity, price])
        return cleaned_data

    def create_dataframe(self, raw_data, server_info, current_time):
        matches = self._extract_records(raw_data)
        cleaned_data = self._process_matches(matches)
        server_name = self._extract_server_name(server_info)
        columns = ["物品", "品质", "等级", "数量", "一口价", "服务器", "时间"]

        # 将服务器名称添加到每一行数据中
        for row in cleaned_data:
            row.append(server_name)
            row.append(current_time)

        df = pd.DataFrame(cleaned_data, columns=columns)
        df['时间'] = pd.to_datetime(df['时间'], format='%Y%m%d%H%M%S')

        return df


def data_cleaning(auction_data, server_info, current_time):
    processor = DataProcessor()
    df = processor.create_dataframe(auction_data, server_info, current_time)
    return df


if __name__ == "__main__":
    processor = DataProcessor()

    # 示例原始数据
    auction_data = '''
    散发阴冷气息的冰柱 仙品 0  1880000
    冰灵珠·仙 灵品 0 13 3050000
    配方：稀世·怨憎会 灵品 0 1 90000
    '''

    # 示例服务器信息
    server_info = "15 qr 16 阿 阿巴 050一剑诛仙线路01 0:09:36"
    current_time = '20250125214636'
    # 创建 DataFrame
    df = processor.create_dataframe(auction_data, server_info, current_time)

    # 输出 DataFrame
    print(df)
    if not os.path.exists('cleaned_data'):
        os.makedirs('cleaned_data')
    # 文件按时间命名
    filename = f'test_{current_time}.csv'
    file_path = os.path.join('cleaned_data', filename)
    df.to_csv(file_path, index=False)
