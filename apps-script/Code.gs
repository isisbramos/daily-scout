const SHEET_ID = "1ToD2eW-owhGsdE0cswVHNGiX8yHJH87Mdtviz-l6kuM";
const SHEET_NAME = "feedback";
const VALID_RATINGS = ["fire", "solid", "meh"];
// Nome do cabeçalho (linha 1) da coluna de comentário — a Isis cria a coluna
// manualmente na planilha; o código acha ela pelo nome, não por posição fixa.
const COMMENT_HEADER = "comentário";

// Acha o índice (1-based) da coluna cujo cabeçalho (linha 1) bate com `header`,
// case-insensitive. Retorna -1 se não achar (coluna ainda não criada/renomeada).
function findColumnByHeader_(sheet, header) {
  const lastCol = sheet.getLastColumn();
  if (lastCol < 1) return -1;
  const headerRow = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
  const target = header.trim().toLowerCase();
  for (let i = 0; i < headerRow.length; i++) {
    if (String(headerRow[i]).trim().toLowerCase() === target) return i + 1;
  }
  return -1;
}
function doPost(e) { try { const data=JSON.parse(e.postData.contents); if (data.type === "comment") return handleComment(data); return handleFeedback(data); } catch (err) { return jsonResponse({ ok: false, error: err.message }); } }
function doGet(e) { const p = (e && e.parameter) || {}; if (p.to) return handleClick(p); if (p.type === "comment") { handleComment({ edition: p.edition||"", rating: p.rating||"", comment: p.comment||"" }); return HtmlService.createHtmlOutput('<html><body style="background:#0F172A"></body></html>'); } handleFeedback({ edition: p.edition||"", rating: p.rating||"", referrer: p.referrer||"direct" }); return HtmlService.createHtmlOutput('<html><body style="background:#0F172A;color:#22C55E;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;margin:0"><div style="text-align:center"><div style="font-size:32px">✓</div><div style="margin-top:12px">Feedback recebido!</div></div></body></html>'); }
// Camada 2: loga o clique por achado na aba "clicks" e redireciona pra fonte. Nunca bloqueia o redirect.
function handleClick(p) { const to=String(p.to||""); if(!/^https?:\/\//i.test(to))return HtmlService.createHtmlOutput("invalid url"); try{ const ss=SpreadsheetApp.openById(SHEET_ID); const sh=ss.getSheetByName("clicks")||ss.insertSheet("clicks"); sh.appendRow([new Date().toISOString(), parseInt(String(p.ed||"").replace(/[^0-9]/g,""))||"", String(p.id||"").substring(0,20), String(p.aud||"").substring(0,40), String(p.src||"").substring(0,40), String(p.claim||"").substring(0,20), to.substring(0,500)]); }catch(err){} return HtmlService.createHtmlOutput('<!DOCTYPE html><html><body style="background:#0F172A"><script>location.replace('+JSON.stringify(to)+');</script></body></html>'); }
// Comentário qualitativo opcional pós-rating. Vai na MESMA linha do clique, na
// coluna cujo cabeçalho é COMMENT_HEADER (a Isis cria essa coluna manualmente
// na planilha) — não numa aba separada. Procura de baixo pra cima a última
// linha dessa edição+rating ainda sem comentário e preenche nela.
// feedback_join.py só lê colunas B/C (edition/rating) por índice, então essa
// coluna nunca quebra o cálculo de fire/solid/meh/n/avg, esteja ela onde estiver.
// Falha muda (try/catch mudo), nunca sobe erro pro leitor.
function handleComment(data) {
  try {
    const edition = String(data.edition||"").replace(/[^0-9]/g,"");
    const rating = String(data.rating||"").toLowerCase();
    const comment = String(data.comment||"").trim().substring(0,500);
    if (!edition || !comment) return jsonResponse({ok:false,error:"missing edition or comment"});
    const sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName(SHEET_NAME);
    if (!sheet) return jsonResponse({ok:false,error:"sheet not found"});
    const commentCol = findColumnByHeader_(sheet, COMMENT_HEADER);
    if (commentCol === -1) return jsonResponse({ok:false,error:"comment column not found"});
    const values = sheet.getDataRange().getValues();
    for (let i = values.length - 1; i >= 0; i--) {
      const row = values[i];
      if (String(row[1]) === edition && String(row[2]).toLowerCase() === rating && !row[commentCol - 1]) {
        sheet.getRange(i + 1, commentCol).setValue(comment);
        return jsonResponse({ok:true});
      }
    }
    // Não achou a linha do rating (raro — GET fallback fora de ordem, etc.):
    // grava como linha própria em vez de perder o comentário.
    const newRow = sheet.getLastRow() + 1;
    sheet.getRange(newRow, 1).setValue(new Date().toISOString());
    sheet.getRange(newRow, 2).setValue(parseInt(edition));
    sheet.getRange(newRow, 3).setValue(rating);
    sheet.getRange(newRow, commentCol).setValue(comment);
    return jsonResponse({ok:true});
  } catch (err) { return jsonResponse({ok:false,error:err.message}); }
}

function handleFeedback(data) { const edition=String(data.edition||"").replace(/[^0-9]/g,""),rating=String(data.rating||"").toLowerCase(),referrer=String(data.referrer||"unknown").substring(0,200); if(!edition)return jsonResponse({ok:false,error:"missing edition"}); if(!VALID_RATINGS.includes(rating))return jsonResponse({ok:false,error:"invalid rating"}); const sheet=SpreadsheetApp.openById(SHEET_ID).getSheetByName(SHEET_NAME); if(!sheet)return jsonResponse({ok:false,error:"sheet not found"}); sheet.appendRow([new Date().toISOString(),parseInt(edition),rating,referrer]); return jsonResponse({ok:true,edition,rating}); }
function jsonResponse(data) { return ContentService.createTextOutput(JSON.stringify(data)).setMimeType(ContentService.MimeType.JSON); }
