import re
import sqlite3


# 执行sql语句
def execute_sql_file(database_path, sql_file_path):
    """连接SQLite数据库并执行SQL文件"""
    print("连接SQLite数据库并执行SQL文件！")
    conn = None
    try:
        # 连接到SQLite数据库（如果不存在会自动创建）
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # 读取SQL文件内容
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # 执行SQL脚本
        cursor.executescript(sql_script)

        # 提交事务
        conn.commit()
        print("SQL脚本执行成功！")

    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
    except FileNotFoundError:
        print(f"错误：SQL文件未找到 - {sql_file_path}")
    except Exception as e:
        print(f"未知错误: {e}")
    finally:
        if conn:
            conn.close()


def sanitize_sql_value(value):
    """处理SQL值中的特殊字符（单引号转义）"""
    return value.replace("'", "·")


# 将mark当文件转成sql
def parse_md_to_sql(md_file_path, sql_file_path):
    with open(md_file_path, 'r', encoding='utf-8') as md_file:
        lines = md_file.readlines()

    # 定位分类树部分
    start_index = None
    for i, line in enumerate(lines):
        if re.match(r'^##\s+分类树', line.strip()):
            start_index = i + 1
            break

    if start_index is None:
        raise ValueError("未找到'## 分类树'章节")

    with open(sql_file_path, 'w', encoding='utf-8') as sql_file:
        sql_file.write("""-- 中国图书馆分类法数据\n""")

        current_hierarchy = []
        parent_stack = []
        indent_unit = 4  # 缩进单位（每级2个空格）

        # 统计重复出现的条目
        exist_codes = set()
        for line in lines[start_index:]:
            line = line.rstrip('\n')

            # 处理顶级分类 (###)
            if re.match(r'^###\s+', line):
                parts = line[4:].split(maxsplit=1)
                if len(parts) < 2:
                    continue

                code, name = parts[0], sanitize_sql_value(parts[1])
                current_hierarchy = [code]
                parent_stack = [None]

                # 生成单行INSERT语句
                sql = f"""INSERT INTO CHINESE_LIBRARY_CLASSIFICATION (CODE, PARENT_CODE, NAME, NAME_EN, DESCRIPTION) 
VALUES ('{code}', NULL, '{name}', '', '');\n"""
                sql_file.write(sql)

            # 处理列表项 (*)
            elif '*' in line:
                indent = len(line) - len(line.lstrip(' '))
                level = indent // indent_unit

                content = line.strip().lstrip('*').strip()
                parts = content.split(maxsplit=1)
                if len(parts) < 2:
                    continue

                raw_code, raw_name = parts[0], parts[1]
                code = raw_code.strip()
                name = sanitize_sql_value(raw_name.strip())

                # 维护层级关系
                if level >= len(parent_stack):
                    parent_stack.append(code)
                else:
                    parent_stack = parent_stack[:level + 1]
                    parent_stack[level] = code

                # 获取父级代码
                parent_code = parent_stack[level - 1] if level > 0 else current_hierarchy[0]

                # 生成单行INSERT语句
                sql = f"""INSERT INTO CHINESE_LIBRARY_CLASSIFICATION  (CODE, PARENT_CODE, NAME, NAME_EN, DESCRIPTION)
VALUES ('{code}', '{parent_code}', '{name}', '', '');\n"""
                if code in exist_codes:
                    print(f'''重复元素: {code}''')
                exist_codes.add(code)
                sql_file.write(sql)


# 处理英文名称
def generate_en_updates(md_file_path, sql_file_path):
    """
    从Markdown文件解析英文分类数据并生成UPDATE语句
    :param md_file_path: Markdown文件路径
    :param sql_file_path: 输出的SQL文件路径
    """
    with open(md_file_path, 'r', encoding='utf-8') as md_file:
        lines = md_file.readlines()

    # 定位分类树部分
    start_index = None
    for i, line in enumerate(lines):
        if re.match(r'^##\s+Classification tree', line.strip(), re.IGNORECASE):
            start_index = i + 1
            break

    if start_index is None:
        raise ValueError("未找到'## Classification tree'章节")

    with open(sql_file_path, 'w', encoding='utf-8') as sql_file:
        sql_file.write("-- 中国图书馆分类法英文名称更新\n")

        for line in lines[start_index:]:
            line = line.strip()

            # 匹配分类条目格式：
            # 格式1: ### Class [CODE] – [NAME_EN]
            # 格式2: * Subclass [CODE] – [NAME_EN]
            if re.match(r'^(###|\*)\s+(Class|Subclass)', line, re.IGNORECASE):
                # 提取代码和英文名称
                parts = re.split(r'\s+–\s+', line, maxsplit=1)
                if len(parts) != 2:
                    continue

                # 提取分类代码
                code_part = parts[0].split()[-1]
                code = re.sub(r'[^A-Za-z0-9]', '', code_part).upper()

                # 处理英文名称
                name_en = sanitize_sql_value(parts[1].strip())

                # 生成UPDATE语句
                update_sql = f"""UPDATE CHINESE_LIBRARY_CLASSIFICATION
SET NAME_EN = '{name_en}'
WHERE CODE = '{code}';"""

                sql_file.write(update_sql + '\n\n')


if __name__ == "__main__":
    # execute_sql_file(
    #     database_path="library_classification.db",  # 数据库文件路径
    #     sql_file_path="library_classification_create.sql"  # SQL文件路径
    # )
    # print("初始化数据库成功！")

    # 生成插入语句
    parse_md_to_sql(
        md_file_path="library_classification/中国图书馆分类法（第5版）.md",
        sql_file_path="library_classification_insert.sql"
    )
    print("生成插入语句成功！")

    # execute_sql_file(
    #     database_path="library_classification.db",  # 数据库文件路径
    #     sql_file_path="library_classification_insert.sql"  # SQL文件路径
    # )
    # print("执行插入语句成功！")

    ## 更新英文名
    generate_en_updates(
        md_file_path="library_classification/Library_of_Congress_Classification.md",
        sql_file_path="library_classification_update_en.sql"
    )
    print("生成更新语句成功！")

    # execute_sql_file(
    #     database_path="library_classification.db",  # 数据库文件路径
    #     sql_file_path="library_classification_update_en.sql"  # SQL文件路径
    # )
    # print("执行更新语句成功！")
