case'img': {
 if (!text) return m.reply(` Example: ${prefix + command} car 10`);

 const gis = require('g-i-s');
 let parts = text.split(" ");
 let count = 5;
 let query = text;

 if (!isNaN(parts[parts.length - 1])) {
 count = parseInt(parts.pop());
 query = parts.join(" ");
 }

 gis(query, async (error, results) => {
 if (error || !results.length) {
 return m.reply('No images found.');
 }
 try {
 let images = results.slice(0, count);
 for (let img of images) {
 await naze.sendMessage(
 m.chat,
 { image: { url: img.url } },
 { quoted: m }
 );
 }
 } catch (e) {
 console.log(e);
 return m.reply('❌ Error while fetching images.');
 }
 });
}
break
