export function getParagraphs(content) {
  return (content || '').split('\n').filter(s => s.trim())
}

export function extractHeader(content) {
  const paras = getParagraphs(content)
  return { title: paras[0] || '', nameLine: paras[1] || '' }
}

function nameLineFor(name) {
  return '——' + (name || '').trim()
}

export function ensureContentHeader(content, title, name) {
  const paras = getParagraphs(content)
  const t = (title || '').trim()
  const nl = nameLineFor(name)
  const out = []
  const changed = []
  let idx = 0

  if (!paras[0] || paras[0] === t) {
    if (paras[0]) out.push(paras[0])
    idx = 1
  } else {
    out.push(t)
    changed.push('title')
  }

  const second = paras[idx]
  if (second === nl) {
    out.push(second)
    idx += 1
  } else if (second && second.startsWith('——')) {
    out.push(nl)
    changed.push('name')
    idx += 1
  } else {
    out.push(nl)
    changed.push('name')
  }

  out.push(...paras.slice(idx))
  return { text: out.join('\n'), changed }
}

export function firstLineTitle(content) {
  return getParagraphs(content)[0] || ''
}