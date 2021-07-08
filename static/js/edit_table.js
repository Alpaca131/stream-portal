/*
 * appendRow: テーブルに行を追加
 */
function appendRow()
{
    const objTBL = document.getElementById("tbl");
    if (!objTBL)
        return;

    const count = objTBL.rows.length;

    // 最終行に新しい行を追加
    const row = objTBL.insertRow(1);

    // 列の追加
    const c1 = row.insertCell(0);
    const c2 = row.insertCell(1);
    const c3 = row.insertCell(2);

    // 各列にスタイルを設定
    c1.className = "text-nowrap sorting_1";
    c2.className = "text-nowrap sorting_1";
    c3.className = "text-nowrap";

    // 各列に表示内容を設定
    c1.innerHTML = '<input class="inpval" type="text" id="word' + count + '" name="word' + count + '" style="border:1px solid #888;">';
    c2.innerHTML = '<input class="inpval" type="text" id="read' + count + '" name="read' + count + '" style="border:1px solid #888;">';
    c3.innerHTML = '<input class="btn btn-twitter edtbtn" type="button" id="edtBtn' + count + '" value="確定" onclick="editRow(this)"><input class="btn btn-danger" type="button" id="delBtn' + count + '" value="削除" onclick="deleteRow(this)">';

    // 追加した行の入力フィールドへフォーカスを設定
    const objInp = document.getElementById("word" + count);
    if (objInp)
        objInp.focus();
}

/*
 * deleteRow: 削除ボタン該当行を削除
 */
function deleteRow(obj)
{
    let i;
// 確認
    if (!confirm("この行を削除しますか？"))
        return;

    if (!obj)
        return;

    const objTR = obj.parentNode.parentNode;
    const objTBL = objTR.parentNode;

    if (objTBL)
        objTBL.deleteRow(objTR.sectionRowIndex);

    // <span> 行番号ふり直し
    let tagElements = document.getElementsByTagName("span");
    if (!tagElements)
        return false;

    let seq = 1;
    for (i = 0; i < tagElements.length; i++)
    {
        if (tagElements[i].className.match("seqno"))
            tagElements[i].innerHTML = seq++;
    }

    // id/name ふり直し
    tagElements = document.getElementsByTagName("input");
    if (!tagElements)
        return false;

    // <input type="text" id="txtN">
    const table = document.getElementById("tbl")
    seq = table.rows.length-1;
    for (i = 0; i < tagElements.length; i++)
    {
        if (tagElements[i].className.match("inpval"))
        {
            if (tagElements[i].id.match(/word\d+/))
            {
                tagElements[i].setAttribute("id", "word" + seq);
                tagElements[i].setAttribute("name", "word" + seq);
                seq--
            }
        }
    }
    seq = table.rows.length-1;
    for (i = 0; i < tagElements.length; i++)
    {
        if (tagElements[i].className.match("inpval"))
        {
            if (tagElements[i].id.match(/read\d+/))
            {
                tagElements[i].setAttribute("id", "read" + seq);
                tagElements[i].setAttribute("name", "read" + seq);
                seq--
            }
        }
    }
    // <input type="button" id="edtBtnN">
    seq = table.rows.length-1;
    for (i = 0; i < tagElements.length; i++)
    {
        if (tagElements[i].className.match("edtbtn"))
        {
            tagElements[i].setAttribute("id", "edtBtn" + seq);
            --seq;
        }
    }

    // <input type="button" id="delBtnN">
    seq = table.rows.length-1;
    for (i = 0; i < tagElements.length; i++)
    {
        if (tagElements[i].className.match("delbtn"))
        {
            tagElements[i].setAttribute("id", "delBtn" + seq);
            ++seq;
        }
    }
}

/*
 * editRow: 編集ボタン該当行の内容を入力・編集またモード切り替え
 */
function editRow(obj)
{
    const objTR = obj.parentNode.parentNode;
    const rowIndex = objTR.sectionRowIndex;
    const table = document.getElementById("tbl")
    const rowId = table.rows.length-rowIndex-1
    const objWord = document.getElementById("word" + rowId);
    const objRead = document.getElementById("read" + rowId);
    const objBtn = document.getElementById("edtBtn" + rowId);

    if (!objWord || !objBtn)
        return;

    // モードの切り替えはボタンの値で判定
    if (objBtn.value === "編集")
    {
        objWord.style.cssText = "border:1px solid #888;"
        objRead.style.cssText = "border:1px solid #888;"
        objWord.readOnly = false;
        objRead.readOnly = false;
        objWord.focus();
        objBtn.value = "確定";
    }
    else
    {
        objWord.style.cssText = "border:none;"
        objRead.style.cssText = "border:none;"
        objWord.readOnly = true;
        objRead.readOnly = true;
        objBtn.value = "編集";
    }
}