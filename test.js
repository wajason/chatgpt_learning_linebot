// 載入學生學習資料 測試ID：U158fae93572222a1d11006515b412205 可改
fetch("sturesp/allData/Ueff707dbb373a21ccefbf2bbe73f4013.json")
  .then((response) => response.json())
  .then((data) => {
    var tableBody = document.querySelector("#data_table tbody");

    // 資料加入表格
    for (var [studentId, studentData] of Object.entries(data)) {
      var row = document.createElement("tr");

      var idCell = document.createElement("td");
      idCell.textContent = studentId;
      row.appendChild(idCell);

      var okQnumCell = document.createElement("td");
      okQnumCell.textContent = studentData.stu_okQnum.join(", ");
      row.appendChild(okQnumCell);

      var ranQCell = document.createElement("td");
      ranQCell.textContent = studentData.stu_ranQ;
      row.appendChild(ranQCell);

      var countOkQCell = document.createElement("td");
      countOkQCell.textContent = studentData.count_okQ;
      row.appendChild(countOkQCell);

      tableBody.appendChild(row);
    }
  })
  .catch((error) => console.error(error));