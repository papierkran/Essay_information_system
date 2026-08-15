import JSZip from 'jszip'

const XML_HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'

function escXml(s) {
  return String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&apos;')
}

function colLetter(n) {
  let s = ''
  n = n + 1
  while (n > 0) {
    const m = (n - 1) % 26
    s = String.fromCharCode(65 + m) + s
    n = Math.floor((n - 1) / 26)
  }
  return s
}

function sheetXml(headers, rows) {
  const lines = ['<sheetData>']
  const all = [headers, ...rows]
  all.forEach((row, ri) => {
    const cells = row.map((v, ci) => {
      const ref = colLetter(ci) + (ri + 1)
      if (typeof v === 'number' && isFinite(v)) {
        return `<c r="${ref}"><v>${v}</v></c>`
      }
      return `<c r="${ref}" t="inlineStr"><is><t>${escXml(v)}</t></is></c>`
    })
    lines.push(`<row r="${ri + 1}">${cells.join('')}</row>`)
  })
  lines.push('</sheetData>')
  const widths = headers.map((h, ci) => {
    const w = Math.min(42, Math.max(12, String(h).length * 2.2 + 4))
    return `<col min="${ci + 1}" max="${ci + 1}" width="${w}" customWidth="1"/>`
  })
  return XML_HEAD + `<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><cols>${widths.join('')}</cols>${lines.join('')}</worksheet>`
}

export async function exportXlsxFile(filename, sheetName, headers, rows) {
  const zip = new JSZip()
  zip.file('[Content_Types].xml', XML_HEAD +
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' +
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>' +
    '<Default Extension="xml" ContentType="application/xml"/>' +
    '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>' +
    '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' +
    '</Types>')
  zip.file('_rels/.rels', XML_HEAD +
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>' +
    '</Relationships>')
  zip.file('xl/workbook.xml', XML_HEAD +
    '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">' +
    `<sheets><sheet name="${escXml(sheetName)}" sheetId="1" r:id="rId1"/></sheets></workbook>`)
  zip.file('xl/_rels/workbook.xml.rels', XML_HEAD +
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>' +
    '</Relationships>')
  zip.file('xl/worksheets/sheet1.xml', sheetXml(headers, rows))
  const blob = await zip.generateAsync({
    type: 'blob',
    mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
