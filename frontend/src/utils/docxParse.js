import JSZip from 'jszip'

export async function readDocxText(file) {
  const zip = await JSZip.loadAsync(file)
  const docXml = await zip.file('word/document.xml').async('string')
  const parser = new DOMParser()
  const xmlDoc = parser.parseFromString(docXml, 'text/xml')
  const paragraphs = xmlDoc.getElementsByTagName('w:p')
  let fullText = ''
  for (const p of paragraphs) {
    const texts = p.getElementsByTagName('w:t')
    let line = ''
    for (const t of texts) {
      line += t.textContent
    }
    fullText += line + '\n'
  }
  return fullText
}

export function extractTitleFromText(text) {
  for (const line of (text || '').split('\n')) {
    const trimmed = line.trim()
    if (!trimmed) continue
    if (/^修改[前后]\s*[：:]?/.test(trimmed)) continue
    if (trimmed.startsWith('——')) continue
    return trimmed.slice(0, 200)
  }
  return ''
}

export function extractNameFromText(text) {
  for (const line of (text || '').split('\n')) {
    const trimmed = line.trim()
    if (trimmed.startsWith('——')) {
      return trimmed.substring(2).trim()
    }
  }
  return ''
}

export async function extractTitleFromFile(file) {
  const name = (file.name || '').toLowerCase()
  try {
    if (name.endsWith('.docx')) {
      return extractTitleFromText(await readDocxText(file))
    }
    if (name.endsWith('.txt')) {
      return extractTitleFromText(await file.text())
    }
  } catch {}
  return ''
}

function findHeading(text, keyword) {
  const re = new RegExp(`^[ \\t]*${keyword}(?:[：:][ \\t]*|[ \\t]+|[ \\t]*(?=$))`, 'gm')
  const m = re.exec(text)
  if (m) return { start: m.index, end: m.index + m[0].length }
  const fb = text.match(new RegExp(`${keyword}[：:]\\s*`))
  if (fb) return { start: fb.index, end: fb.index + fb[0].length }
  return null
}

export function splitBeforeAfterText(text) {
  const afterHead = findHeading(text, '修改后')
  const beforeHead = findHeading(text, '修改前')
  let before = ''
  let after = ''
  if (afterHead) {
    after = text.slice(afterHead.end).trim()
  }
  if (beforeHead) {
    const start = beforeHead.end
    let end = text.length
    if (afterHead && afterHead.start >= start) end = afterHead.start
    before = text.slice(start, end).trim()
  }
  return { before, after }
}
