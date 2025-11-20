// const msg = document.getElementById("msg");
// const chatBox = document.getElementById("chat-box");
// const mic = document.getElementById("mic");
// const send = document.getElementById("send");
// let voiceMode = false;

// /* ---------------- Display Message ---------------- */
// function push(sender, text) {
//   const div = document.createElement("div");
//   div.className = sender === "bot" ? "bot-msg" : "user-msg";
//   div.innerHTML = text;
//   chatBox.appendChild(div);
//   chatBox.scrollTop = chatBox.scrollHeight;
// }

// /* ---------------- Speak Bot Reply (Improved Arabic) ---------------- */
// function speak(text, lang) {
//   if (!voiceMode) return;
//   try {
//     const utter = new SpeechSynthesisUtterance(text.replace(/<[^>]*>?/gm, ""));

//     // Auto-detect Arabic letters in the bot reply
//     if (/[\u0600-\u06FF]/.test(text)) {
//       utter.lang = "ar-SA"; // Force Arabic voice
//     } else {
//       utter.lang = "en-US"; // English voice
//     }

//     utter.rate = 1;
//     speechSynthesis.cancel();
//     speechSynthesis.speak(utter);
//   } catch (e) {
//     console.warn("Speech synthesis issue:", e);
//   }
// }

// /* ---------------- Clean Voice Output ---------------- */
// function cleanVoiceReply(fullReply, lang) {
//   if (fullReply.includes("Welcome to JOANA Fast Food")) {
//     return lang === "ar"
//       ? "مرحبا بك في مطعم جوانا. هل ترغب في الطلب؟"
//       : "Welcome to JOANA Fast Food! Ready to order?";
//   }

//   let clean = fullReply
//     .split("<br>")[0]
//     .replace(/<[^>]*>?/gm, "")
//     .trim();

//   if (clean.length < 2) clean = fullReply.replace(/<[^>]*>?/gm, "").trim();
//   return clean;
// }

// /* ---------------- Send to Backend ---------------- */
// async function sendMessage(userText = null) {
//   const text = userText || msg.value.trim();
//   if (!text) return;

//   push("user", text);
//   msg.value = "";

//   const res = await fetch("/api/chat", {
//     method: "POST",
//     headers: { "Content-Type": "application/json" },
//     body: JSON.stringify({ message: text, is_voice: voiceMode }),
//   });

//   const data = await res.json();
//   push("bot", data.reply);

//   if (data.menu && data.menu.endsWith(".PNG")) {
//     push("bot", `<img src="${data.menu}" class="menu-img">`);
//   }

//   const cleanSpeech = cleanVoiceReply(data.reply, data.lang);
//   speak(cleanSpeech, data.lang);
// }

// send.onclick = () => sendMessage();
// msg.addEventListener("keydown", (e) => {
//   if (e.key === "Enter") sendMessage();
// });

// /* ---------------- FIXED DUAL LANGUAGE MIC ---------------- */
// if ("webkitSpeechRecognition" in window) {
//   const rec = new webkitSpeechRecognition();
//   rec.continuous = false;
//   rec.interimResults = false;

//   mic.onclick = () => {
//     mic.classList.add("recording");
//     voiceMode = true;

//     // STEP 1 → Try English first
//     //rec.lang = "en-US";
//     rec.start();
//   };

//   rec.onresult = (e) => {
//     mic.classList.remove("recording");

//     let speech = e.results[0][0].transcript.trim();
//     console.log("Raw:", speech);

//     const hasArabic = /[\u0600-\u06FF]/.test(speech);
//     const hasEnglish = /[A-Za-z]/.test(speech);

//     // ---- CASE A: Recognized as ARABIC ----
//     if (hasArabic && !hasEnglish) {
//       console.log("Detected Arabic → switching to ARABIC mode");
//       rec.lang = "ar-SA";
//       rec.start();
//       return;
//     }

//     // ---- CASE B: Recognized as ENGLISH ----
//     console.log("Detected English");
//     sendMessage(speech);
//   };

//   rec.onerror = () => {
//     console.log("English failed → trying Arabic");
//     rec.lang = "ar-SA";
//     rec.start();
//   };

//   rec.onend = () => mic.classList.remove("recording");
// }

// ____________________________________UPDATED CODE__________________________________

// const msg = document.getElementById("msg");
// const chatBox = document.getElementById("chat-box");
// const mic = document.getElementById("mic");
// const send = document.getElementById("send");

// // Tooltip explaining dual-language mic
// if (mic) {
//   mic.setAttribute(
//     "title",
//     "Click and speak in English or Arabic. The assistant will reply and speak in the same language."
//   );
// }

// /* ---------------- Display Message (safe) ---------------- */
// function push(sender, text, isHtml = false) {
//   const div = document.createElement("div");
//   div.className = sender === "bot" ? "bot-msg" : "user-msg";

//   if (isHtml) {
//     // Only use this when YOU generate the HTML (e.g., menu image)
//     div.innerHTML = text;
//   } else {
//     // For normal user/bot text: avoid XSS
//     div.textContent = text;
//   }

//   chatBox.appendChild(div);
//   chatBox.scrollTop = chatBox.scrollHeight;
// }

// /* ---------------- Speak Bot Reply ---------------- */
// function speak(text) {
//   try {
//     const plain = text.replace(/<[^>]*>?/gm, "");
//     const utter = new SpeechSynthesisUtterance(plain);

//     // Auto-detect Arabic letters in the bot reply
//     if (/[\u0600-\u06FF]/.test(text)) {
//       utter.lang = "ar-SA"; // Saudi Arabic voice
//     } else {
//       utter.lang = "en-US"; // English voice
//     }

//     utter.rate = 1;
//     speechSynthesis.cancel();
//     speechSynthesis.speak(utter);
//   } catch (e) {
//     console.warn("Speech synthesis issue:", e);
//   }
// }

// /* ---------------- Clean Voice Output ---------------- */
// function cleanVoiceReply(fullReply, lang) {
//   if (fullReply.includes("Welcome to JOANA Fast Food")) {
//     return lang === "ar"
//       ? "مرحبا بك في مطعم جوانا. هل ترغب في الطلب؟"
//       : "Welcome to JOANA Fast Food! Ready to order?";
//   }

//   // Handle <br>, <br/>, <br /> etc.
//   const firstLine = fullReply.split(/<br\s*\/?>/i)[0];

//   let clean = firstLine.replace(/<[^>]*>?/gm, "").trim();

//   if (clean.length < 2) {
//     clean = fullReply.replace(/<[^>]*>?/gm, "").trim();
//   }
//   return clean;
// }

// /* ---------------- Send to Backend ---------------- */
// async function sendMessage(userText = null, isVoice = false) {
//   const text = userText || msg.value.trim();
//   if (!text) return;

//   // user text is plain, so not HTML
//   push("user", text, false);
//   msg.value = "";

//   try {
//     const res = await fetch("/api/chat", {
//       method: "POST",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify({ message: text, is_voice: isVoice }),
//     });

//     if (!res.ok) {
//       throw new Error("Server error: " + res.status);
//     }

//     const data = await res.json();

//     // Bot reply might contain HTML (e.g., <br>)
//     push("bot", data.reply, true);

//     if (
//       data.menu &&
//       typeof data.menu === "string" &&
//       data.menu.toUpperCase().endsWith(".PNG")
//     ) {
//       // We control this HTML, so allowed
//       push("bot", `<img src="${data.menu}" class="menu-img">`, true);
//     }

//     const cleanSpeech = cleanVoiceReply(data.reply || "", data.lang || "en");

//     // Only speak if THIS message came from voice input
//     if (isVoice) {
//       speak(cleanSpeech);
//     }
//   } catch (err) {
//     console.error(err);
//     push("bot", "Sorry, something went wrong. Please try again.", false);
//   }
// }

// // Typing → text only (no voice)
// send.onclick = () => sendMessage();
// msg.addEventListener("keydown", (e) => {
//   if (e.key === "Enter") sendMessage();
// });

// /* ---------------- MIC: single button, dual language ---------------- */
// if ("webkitSpeechRecognition" in window) {
//   const rec = new webkitSpeechRecognition();
//   rec.continuous = false;
//   rec.interimResults = false;

//   // Start with Saudi Arabic as the primary language
//   rec.lang = "ar-SA";

//   let triedFallback = false;

//   mic.onclick = () => {
//     mic.classList.add("recording");
//     rec.start();
//   };

//   rec.onresult = (e) => {
//     mic.classList.remove("recording");

//     const speechText = e.results[0][0].transcript.trim();
//     console.log("Raw speech:", speechText);

//     // Voice message: bot should speak & write in detected language
//     sendMessage(speechText, true);
//   };

//   rec.onerror = (event) => {
//     console.log("Speech recognition error:", event.error);
//     mic.classList.remove("recording");

//     // Smooth fallback: if Arabic STT fails once, retry in English automatically
//     if (!triedFallback) {
//       triedFallback = True;
//     }
//   };

//   rec.onend = () => {
//     mic.classList.remove("recording");
//   };
// }

// ------------------CORRECT CODE ___________________

// const msg = document.getElementById("msg");
// const chatBox = document.getElementById("chat-box");
// const mic = document.getElementById("mic");
// const send = document.getElementById("send");

// /* Tooltip on mic: single button, auto language */
// if (mic) {
//   mic.setAttribute(
//     "title",
//     "Click and speak in English or Arabic. The assistant will reply and speak in the same language."
//   );
// }

// /* ---------------- Display Message (safe) ---------------- */
// function push(sender, text, isHtml = false) {
//   const div = document.createElement("div");
//   div.className = sender === "bot" ? "bot-msg" : "user-msg";

//   if (isHtml) {
//     // Only use this when YOU generate the HTML (e.g., menu image)
//     div.innerHTML = text;
//   } else {
//     // For normal user/bot text: avoid XSS
//     div.textContent = text;
//   }

//   chatBox.appendChild(div);
//   chatBox.scrollTop = chatBox.scrollHeight;
// }

// /* ---------------- Speak Bot Reply ---------------- */
// function speak(text) {
//   try {
//     const plain = text.replace(/<[^>]*>?/gm, "");
//     const utter = new SpeechSynthesisUtterance(plain);

//     // Auto-detect Arabic letters in the bot reply
//     if (/[\u0600-\u06FF]/.test(text)) {
//       utter.lang = "ar-SA"; // Arabic TTS
//     } else {
//       utter.lang = "en-US"; // English TTS
//     }

//     utter.rate = 1;
//     speechSynthesis.cancel();
//     speechSynthesis.speak(utter);
//   } catch (e) {
//     console.warn("Speech synthesis issue:", e);
//   }
// }

// /* ---------------- Clean Voice Output ---------------- */
// function cleanVoiceReply(fullReply, lang) {
//   if (fullReply.includes("Welcome to JOANA Fast Food")) {
//     return lang === "ar"
//       ? "مرحبا بك في مطعم جوانا. هل ترغب في الطلب؟"
//       : "Welcome to JOANA Fast Food! Ready to order?";
//   }

//   const firstLine = fullReply.split(/<br\s*\/?>/i)[0];

//   let clean = firstLine.replace(/<[^>]*>?/gm, "").trim();

//   if (clean.length < 2) {
//     clean = fullReply.replace(/<[^>]*>?/gm, "").trim();
//   }
//   return clean;
// }

// /* ---------------- Send to Backend ---------------- */
// async function sendMessage(userText = null, isVoice = false, langHint = null) {
//   const text = userText || msg.value.trim();
//   if (!text) return;

//   // user text is plain, so not HTML
//   push("user", text, false);
//   msg.value = "";

//   try {
//     const res = await fetch("/api/chat", {
//       method: "POST",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify({
//         message: text,
//         is_voice: isVoice,
//         lang_hint: langHint, // voice language hint for backend
//       }),
//     });

//     if (!res.ok) {
//       throw new Error("Server error: " + res.status);
//     }

//     const data = await res.json();

//     // Bot reply might contain HTML (e.g., <br>)
//     push("bot", data.reply, true);

//     if (
//       data.menu &&
//       typeof data.menu === "string" &&
//       data.menu.toUpperCase().endsWith(".PNG")
//     ) {
//       // We control this HTML, so allowed
//       push("bot", `<img src="${data.menu}" class="menu-img">`, true);
//     }

//     const cleanSpeech = cleanVoiceReply(data.reply || "", data.lang || "en");

//     // Only speak if THIS message came from voice input
//     if (isVoice) {
//       speak(cleanSpeech);
//     }
//   } catch (err) {
//     console.error(err);
//     push("bot", "Sorry, something went wrong. Please try again.", false);
//   }
// }

// // Typing → text only (no speech)
// send.onclick = () => sendMessage();
// msg.addEventListener("keydown", (e) => {
//   if (e.key === "Enter") sendMessage();
// });

// /* --------------- Roman Arabic mapping (STRICT) ---------------- */
// // Map of common roman Arabic words -> Arabic script
// const romanArabicMap = {
//   marhaba: "مرحبا",
//   mar7aba: "مرحبا",
//   salam: "سلام",
//   salaam: "سلام",
//   assalam: "السلام",
//   asalam: "السلام",
//   alaikum: "عليكم",
//   shukran: "شكرا",
//   shukranjazeelan: "شكرا جزيلا",
//   jazakallah: "جزاك الله",
//   habibi: "حبيبي",
//   habibti: "حبيبتي",
//   hala: "هلا",
//   ahlan: "أهلا",
//   masalama: "مع السلامة",
// };

// // true only if *all* tokens are in our romanArabicMap
// function isPureRomanArabic(str) {
//   const tokens = str.toLowerCase().split(/\s+/).filter(Boolean);
//   if (!tokens.length) return false;
//   return tokens.every((t) => romanArabicMap[t]);
// }

// function transliterateRomanArabic(str) {
//   const tokens = str.toLowerCase().split(/\s+/).filter(Boolean);
//   return tokens.map((t) => romanArabicMap[t] || t).join(" ");
// }

// /* ---------------- MIC: single button, auto EN/AR detection (no roman output) ---------------- */
// if ("webkitSpeechRecognition" in window) {
//   const rec = new webkitSpeechRecognition();
//   rec.continuous = false;
//   rec.interimResults = false;

//   // Prioritize English recognition quality
//   rec.lang = "en-US";

//   mic.onclick = () => {
//     mic.classList.add("recording");
//     rec.start();
//   };

//   rec.onresult = (e) => {
//     mic.classList.remove("recording");

//     const rawSpeech = e.results[0][0].transcript.trim();
//     console.log("Raw speech:", rawSpeech);

//     let langHint = "en";
//     let finalText = rawSpeech;

//     const hasArabicChars = /[\u0600-\u06FF]/.test(rawSpeech);
//     const hasLatinChars = /[A-Za-z]/.test(rawSpeech);

//     if (hasArabicChars) {
//       // Already real Arabic script
//       langHint = "ar";
//       finalText = rawSpeech;
//     } else if (hasLatinChars && isPureRomanArabic(rawSpeech)) {
//       // It's roman Arabic and we can transliterate every token safely.
//       // Convert fully to Arabic, so NO roman stays in chat.
//       langHint = "ar";
//       finalText = transliterateRomanArabic(rawSpeech);
//     } else {
//       // Everything else is treated as English.
//       // That means ambiguous roman text is considered English, never Arabic.
//       langHint = "en";
//       finalText = rawSpeech;
//     }

//     // Voice message: send finalText (only English OR Arabic letters) and langHint
//     sendMessage(finalText, true, langHint);
//   };

//   rec.onerror = (event) => {
//     console.log("Speech recognition error:", event.error);
//     mic.classList.remove("recording");
//   };

//   rec.onend = () => {
//     mic.classList.remove("recording");
//   };
// }

const msg = document.getElementById("msg");
const chatBox = document.getElementById("chat-box");
const mic = document.getElementById("mic");
const send = document.getElementById("send");

/* Tooltip on mic: single button, auto language */
if (mic) {
  mic.setAttribute(
    "title",
    "Click and speak in English or Arabic. The assistant will reply and speak in the same language."
  );
}

/* ---------------- Display Message (safe) ---------------- */
function push(sender, text, isHtml = false) {
  const div = document.createElement("div");
  div.className = sender === "bot" ? "bot-msg" : "user-msg";

  if (isHtml) {
    // Only use this when YOU generate the HTML (e.g., menu image)
    div.innerHTML = text;
  } else {
    // For normal user/bot text: avoid XSS
    div.textContent = text;
  }

  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

/* ---------------- Speak Bot Reply ---------------- */
function speak(text) {
  try {
    const plain = text.replace(/<[^>]*>?/gm, "");
    const utter = new SpeechSynthesisUtterance(plain);

    // Auto-detect Arabic letters in the bot reply
    if (/[\u0600-\u06FF]/.test(text)) {
      utter.lang = "ar-SA"; // Arabic TTS
    } else {
      utter.lang = "en-US"; // English TTS
    }

    utter.rate = 1;
    speechSynthesis.cancel();
    speechSynthesis.speak(utter);
  } catch (e) {
    console.warn("Speech synthesis issue:", e);
  }
}

/* ---------------- Clean Voice Output ---------------- */
function cleanVoiceReply(fullReply, lang) {
  if (fullReply.includes("Welcome to JOANA Fast Food")) {
    return lang === "ar"
      ? "مرحبا بك في مطعم جوانا. هل ترغب في الطلب؟"
      : "Welcome to JOANA Fast Food! Ready to order?";
  }

  const firstLine = fullReply.split(/<br\s*\/?>/i)[0];

  let clean = firstLine.replace(/<[^>]*>?/gm, "").trim();

  if (clean.length < 2) {
    clean = fullReply.replace(/<[^>]*>?/gm, "").trim();
  }
  return clean;
}

/* ---------------- Send to Backend ---------------- */
async function sendMessage(userText = null, isVoice = false, langHint = null) {
  const text = userText || msg.value.trim();
  if (!text) return;

  // user text is plain, so not HTML
  push("user", text, false);
  msg.value = "";

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        is_voice: isVoice,
        lang_hint: langHint, // voice language hint for backend
      }),
    });

    if (!res.ok) {
      throw new Error("Server error: " + res.status);
    }

    const data = await res.json();

    // Bot reply might contain HTML (e.g., <br>)
    push("bot", data.reply, true);

    if (
      data.menu &&
      typeof data.menu === "string" &&
      data.menu.toUpperCase().endsWith(".PNG")
    ) {
      // We control this HTML, so allowed
      push("bot", `<img src="${data.menu}" class="menu-img">`, true);
    }

    const cleanSpeech = cleanVoiceReply(data.reply || "", data.lang || "en");

    // Only speak if THIS message came from voice input
    if (isVoice) {
      speak(cleanSpeech);
    }
  } catch (err) {
    console.error(err);
    push("bot", "Sorry, something went wrong. Please try again.", false);
  }
}

// Typing → text only (no speech)
send.onclick = () => sendMessage();
msg.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMessage();
});

/* --------------- Roman Arabic mapping (STRICT) ---------------- */
// Map of common roman Arabic words -> Arabic script
const romanArabicMap = {
  marhaba: "مرحبا",
  mar7aba: "مرحبا",
  salam: "سلام",
  salaam: "سلام",
  assalam: "السلام",
  asalam: "السلام",
  alaikum: "عليكم",
  shukran: "شكرا",
  shukranjazeelan: "شكرا جزيلا",
  jazakallah: "جزاك الله",
  habibi: "حبيبي",
  habibti: "حبيبتي",
  hala: "هلا",
  ahlan: "أهلا",
  masalama: "مع السلامة",
};

// true only if *all* tokens are in our romanArabicMap
function isPureRomanArabic(str) {
  const tokens = str.toLowerCase().split(/\s+/).filter(Boolean);
  if (!tokens.length) return false;
  return tokens.every((t) => romanArabicMap[t]);
}

function transliterateRomanArabic(str) {
  const tokens = str.toLowerCase().split(/\s+/).filter(Boolean);
  return tokens.map((t) => romanArabicMap[t] || t).join(" ");
}

/* ---------------- MIC: single button, auto EN/AR detection (no roman output) ---------------- */
if ("webkitSpeechRecognition" in window) {
  const rec = new webkitSpeechRecognition();
  rec.continuous = false;
  rec.interimResults = false;

  // Prioritize English recognition quality
  rec.lang = "en-US";

  mic.onclick = () => {
    mic.classList.add("recording");
    rec.start();
  };

  rec.onresult = (e) => {
    mic.classList.remove("recording");

    const rawSpeech = e.results[0][0].transcript.trim();
    console.log("Raw speech:", rawSpeech);

    let langHint = "en";
    let finalText = rawSpeech;

    const hasArabicChars = /[\u0600-\u06FF]/.test(rawSpeech);
    const hasLatinChars = /[A-Za-z]/.test(rawSpeech);

    if (hasArabicChars) {
      // Already real Arabic script
      langHint = "ar";
      finalText = rawSpeech;
    } else if (hasLatinChars && isPureRomanArabic(rawSpeech)) {
      // It's roman Arabic and we can transliterate every token safely.
      // Convert fully to Arabic, so NO roman stays in chat.
      langHint = "ar";
      finalText = transliterateRomanArabic(rawSpeech);
    } else {
      // Everything else is treated as English.
      // That means ambiguous roman text is considered English, never Arabic.
      langHint = "en";
      finalText = rawSpeech;
    }

    // Voice message: send finalText (only English OR Arabic letters) and langHint
    sendMessage(finalText, true, langHint);
  };

  rec.onerror = (event) => {
    console.log("Speech recognition error:", event.error);
    mic.classList.remove("recording");
  };

  rec.onend = () => {
    mic.classList.remove("recording");
  };
}
