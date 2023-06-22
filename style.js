// 讀取JSON文件
fetch('Questions.json')
  .then(response => response.json())
  .then(data => {
    // 逐一抓取每個問題的標準答案
    Object.values(data).forEach(q => {
      let answer = q['a'];
      console.log(answer);
    });

    // 抓取第一個問題的標準答案
    let answer = data['q1']['a'];
    console.log(answer);
  });


      fetch('./Questions.json')
        .then(response => response.json())
        .then(data => {
          // 抓取第一個問題的標準答案
          let answer = data['q1']['a'];
          console.log(answer);

          // 呈現第一题的答案
          let answerElement = document.getElementById('answer');
          answerElement.textContent = answer;

          // 填充表格单元格
          let table = document.querySelector('table');
          Object.keys(data).forEach((key, index) => {
            if (index > 4) {
              return;
            }

            let q = data[key]['q'];
            let a = data[key]['a'];
            let cell = table.rows[1].cells[index];

            cell.textContent = `答案：${a}, 答對率：10/23`;
          });
        });
