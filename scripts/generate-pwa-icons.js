// Script to generate PWA icons from Logo ZMO.png
// Usage: node scripts/generate-pwa-icons.js

import sharp from 'sharp';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { existsSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootDir = join(__dirname, '..');

const logoPath = join(rootDir, 'static', 'Logo ZMO.png');
const staticDir = join(rootDir, 'static');

async function generateIcons() {
	console.log('🎨 Generating PWA icons from Logo ZMO.png...\n');

	if (!existsSync(logoPath)) {
		console.error('❌ Error: Logo ZMO.png not found in static folder');
		console.error('   Please ensure the file exists at:', logoPath);
		process.exit(1);
	}

	try {
		// Generate 192x192 icon
		await sharp(logoPath)
			.resize(192, 192, {
				fit: 'contain',
				background: { r: 255, g: 255, b: 255, alpha: 1 }
			})
			.png()
			.toFile(join(staticDir, 'pwa-192x192.png'));
		console.log('✅ Generated pwa-192x192.png');

		// Generate 512x512 icon
		await sharp(logoPath)
			.resize(512, 512, {
				fit: 'contain',
				background: { r: 255, g: 255, b: 255, alpha: 1 }
			})
			.png()
			.toFile(join(staticDir, 'pwa-512x512.png'));
		console.log('✅ Generated pwa-512x512.png');

		// Generate Apple touch icon (180x180)
		await sharp(logoPath)
			.resize(180, 180, {
				fit: 'contain',
				background: { r: 255, g: 255, b: 255, alpha: 1 }
			})
			.png()
			.toFile(join(staticDir, 'apple-touch-icon.png'));
		console.log('✅ Generated apple-touch-icon.png');

		// Generate favicon.ico (32x32)
		// Note: Sharp doesn't directly support .ico, so we create a 32x32 PNG
		// Browsers will accept PNG as favicon if named favicon.png
		await sharp(logoPath)
			.resize(32, 32, {
				fit: 'contain',
				background: { r: 255, g: 255, b: 255, alpha: 1 }
			})
			.png()
			.toFile(join(staticDir, 'favicon.png'));
		console.log('✅ Generated favicon.png (32x32)');

		// Also generate a 16x16 version for older browsers
		await sharp(logoPath)
			.resize(16, 16, {
				fit: 'contain',
				background: { r: 255, g: 255, b: 255, alpha: 1 }
			})
			.png()
			.toFile(join(staticDir, 'favicon-16x16.png'));
		console.log('✅ Generated favicon-16x16.png');

		console.log('\n🎉 All PWA icons generated successfully!');
		console.log('\n📝 Note: Sharp doesn\'t create .ico files directly.');
		console.log('   Using favicon.png instead (widely supported by modern browsers).');
		console.log('   To create a true .ico file, use an online tool like favicon.io');
		console.log('\nNext steps:');
		console.log('1. Run: npm run build');
		console.log('2. Run: npm run preview');
		console.log('3. Check for the install button in your browser!');
	} catch (error) {
		console.error('❌ Error generating icons:', error.message);
		process.exit(1);
	}
}

generateIcons();
