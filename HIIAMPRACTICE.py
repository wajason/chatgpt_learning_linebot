  # 檢查檔案是否存在，如果存在就讀取之前的資料，否則建立一個新的檔案
  if os.path.isfile('sturecord.html'):
    with open('sturecord.html', 'r', encoding='utf-8') as f:
      previous_data = f.readlines()
      # 只保留前58行的內容
      previous_data = previous_data[:58]
  else:
    previous_data = []

  # 取得路徑下對應的txt檔案
  txt_files = [f for f in os.listdir('sturesp/allresp/{userid}.txt') ]

  # 創建一個 dictionary 來儲存每個使用者最新的 DataFrame
  user_tables = {}

  # 逐一讀取每個txt檔案，整理成DataFrame，並存儲在 user_tables 中
  for txt_file in txt_files:
    user_id = txt_file.split('.')[0]
    with open(f'sturesp/allresp/{txt_file}', 'r') as f:
      data = [eval(line) for line in f]

    # 提取 ID、時間、訊息
    rows = []
    for item in data:
      rows.append({'ID': item['ID'], '時間': item['時間'], '訊息': item['訊息']})

    # 將資料轉換成 DataFrame
    df = pd.DataFrame(rows)

    # 如果使用者已經有表格，則將新的訊息更新至原表格，否則就新增一個新表格
    if user_id in user_tables:
      # 找出更新後的資料
      updated_df = df[df['時間'] > user_tables[user_id]['時間'].max()]
      if not updated_df.empty:
        # 將更新後的表格與原本的表格合併
        user_tables[user_id] = pd.concat([user_tables[user_id], updated_df])
    else:
      user_tables[user_id] = df

  # 將每個使用者的 DataFrame 轉換成 HTML 表格，並連接起來
  html_tables = []
  for user_id, df in user_tables.items():
    html_tables.append(f"<h2>{user_id}</h2>" + df.to_html(index=False))

  all_html_tables = '<br>'.join(html_tables)

  # 在 sturecord.html 檔案的末尾繼續添加 HTML 表格
  with open('sturecord.html', 'w', encoding='utf-8') as f:
    # 將表格包裝在一個<div>元素中，加上padding-left樣式屬性讓表格向右移
    htmljump = """<!-- Option 1: jQuery and Bootstrap Bundle (includes Popper) -->
    <script src="https://cdn.jsdelivr.net/npm/jquery@3.5.1/dist/jquery.slim.min.js" integrity="sha384-DfXdz2htPH0lsSSs5nCTpuj/zy4C+OGpamoFVy38MVBnE+IbbVYUew+OrCXaRkfj" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js" integrity="sha384-Fy6S3B9q64WdZWQUiU+q4/2Lc9npb8tCaSX9FK7E8HnRr0Jz8D6OP9dO5Vg3Q9ct" crossorigin="anonymous"></script>
</body>
</html>"""
    html = f"<div style='text-align:center; padding-left: 50px;'>{all_html_tables}</div>{htmljump}"
    f.write(''.join(previous_data) + html)