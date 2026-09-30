import { closeSync, openSync, readdirSync, readSync } from 'node:fs'
import { relative, resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

const imagesDirectory = fileURLToPath(new URL('./public/images', import.meta.url))
const eventImagesModuleId = 'virtual:event-images'
const resolvedEventImagesModuleId = `\0${eventImagesModuleId}`

function isHeifImage(filePath) {
  const descriptor = openSync(filePath, 'r')
  const header = Buffer.alloc(12)

  try {
    readSync(descriptor, header, 0, header.length, 0)
  } finally {
    closeSync(descriptor)
  }

  return ['heic', 'heix', 'hevc', 'hevx', 'mif1', 'msf1'].includes(
    header.toString('ascii', 8, 12),
  )
}

function eventImagesPlugin() {
  return {
    name: 'event-images',
    resolveId(id) {
      if (id === eventImagesModuleId) return resolvedEventImagesModuleId
    },
    load(id) {
      if (id !== resolvedEventImagesModuleId) return null

      const imagePaths = []
      const collectImages = (directory) => {
        for (const entry of readdirSync(directory, { withFileTypes: true })) {
          const filePath = resolve(directory, entry.name)
          if (entry.isDirectory()) {
            if (!['hero', 'logo'].includes(entry.name.toLowerCase())) collectImages(filePath)
          } else if (
            /\.(avif|gif|jpe?g|png|webp)$/i.test(entry.name) &&
            !isHeifImage(filePath)
          ) {
            const relativePath = relative(imagesDirectory, filePath).split(sep).join('/')
            imagePaths.push(`images/${relativePath}`)
          }
        }
      }

      collectImages(imagesDirectory)
      imagePaths.sort((left, right) => left.localeCompare(right, 'it'))

      const images = imagePaths.map((src, index) => ({
        src,
        alt: `Foto ${index + 1} della galleria eventi`,
      }))

      return `export const eventImages = ${JSON.stringify(images)}`
    },
  }
}

export default defineConfig({
  plugins: [react(), tailwindcss(), eventImagesPlugin()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
    watch: {
      usePolling: true,
      interval: 100,
    },
  },
})
