export function formatDateTime(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  if (isNaN(d.getTime())) return isoStr
  
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hour = String(d.getHours()).padStart(2, '0')
  const minute = String(d.getMinutes()).padStart(2, '0')
  
  return `${year}-${month}-${day} ${hour}:${minute}`
}

export function formatDate(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  if (isNaN(d.getTime())) return isoStr
  
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  
  return `${year}-${month}-${day}`
}

export function countWords(text) {
  if (!text) return 0
  let count = 0
  for (const c of text) {
    if (!/\s/.test(c)) count++
  }
  return count
}
