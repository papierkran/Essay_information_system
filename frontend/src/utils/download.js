export function downloadBlobResponse(res, fallbackName) {
  const disposition = res.headers?.['content-disposition'] || ''
  let filename = fallbackName
  if (disposition) {
    const p = disposition.split(';')
    for (const part of p) {
      const trim = part.trim()
      if (trim.startsWith('filename*=')) {
        const val = trim.split("''").pop()
        if (val) filename = decodeURIComponent(val.replace(/"/g, ''))
        break
      } else if (trim.startsWith('filename=')) {
        const val = trim.split('=')[1]
        if (val) filename = val.replace(/"/g, '')
      }
    }
  }
  const url = window.URL.createObjectURL(new Blob([res.data]))
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  window.URL.revokeObjectURL(url)
}
