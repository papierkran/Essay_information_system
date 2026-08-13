const IMAGE_MAX_DIM = 4000
const IMAGE_MAX_BYTES = 2 * 1024 * 1024

function isImageFile(file) {
  return file.type && file.type.startsWith('image/')
}

function loadImage(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const img = new Image()
    img.onload = () => {
      URL.revokeObjectURL(url)
      resolve(img)
    }
    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('图片解码失败'))
    }
    img.src = url
  })
}

function canvasToBlob(canvas, type, quality) {
  return new Promise((resolve, reject) => {
    canvas.toBlob(b => (b ? resolve(b) : reject(new Error('toBlob 失败'))), type, quality)
  })
}

function makeOutName(originalName, outType) {
  const ext = outType === 'image/webp' ? 'webp' : outType === 'image/png' ? 'png' : 'jpg'
  const base = (originalName || 'image').replace(/\.[^.]+$/, '')
  return base + '.' + ext
}

function blobToFile(blob, originalFile, outType) {
  return new File([blob], makeOutName(originalFile.name, outType), {
    type: outType,
    lastModified: originalFile.lastModified,
  })
}

export async function compressImageFile(file) {
  if (!isImageFile(file)) return file
  if (file.size <= IMAGE_MAX_BYTES) return file

  let img
  try {
    img = await loadImage(file)
  } catch (e) {
    return file
  }

  const { naturalWidth: w, naturalHeight: h } = img
  if (!w || !h) return file

  const scale = Math.min(1, IMAGE_MAX_DIM / Math.max(w, h))
  if (scale === 1 && file.size <= IMAGE_MAX_BYTES) return file

  const canvas = document.createElement('canvas')
  canvas.width = Math.round(w * scale)
  canvas.height = Math.round(h * scale)
  const ctx = canvas.getContext('2d')
  ctx.fillStyle = '#fff'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  ctx.drawImage(img, 0, 0, canvas.width, canvas.height)

  const outType = file.type === 'image/webp' ? 'image/webp' : 'image/jpeg'

  let best = null
  for (const quality of [0.85, 0.75, 0.65, 0.55, 0.45]) {
    let blob
    try {
      blob = await canvasToBlob(canvas, outType, quality)
    } catch (e) {
      return best ? blobToFile(best, file, outType) : file
    }
    if (blob.size <= IMAGE_MAX_BYTES) {
      return blobToFile(blob, file, outType)
    }
    if (!best || blob.size < best.size) best = blob
  }
  return best ? blobToFile(best, file, outType) : file
}

export async function compressImageFiles(files) {
  const list = Array.isArray(files) ? files : [files]
  const results = await Promise.all(list.map(f => compressImageFile(f)))
  return Array.isArray(files) ? results : results[0]
}