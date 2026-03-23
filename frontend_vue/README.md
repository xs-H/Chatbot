# frontend structure
```
frontend-vue/
├─ index.html
├─ package.json
├─ vite.config.js
├─ public/
│  └─ images/
│     ├─ logo.png
│     ├─ avatar.jpg
│     └─ character.jpg
└─ src/
   ├─ main.js
   ├─ App.vue
   ├─ assets/
   │  └─ main.css
   ├─ components/
   │  ├─ AppSidebar.vue
   │  ├─ TopActions.vue
   │  ├─ IntroPanel.vue
   │  ├─ ChatBox.vue
   │  ├─ ChatMessages.vue
   │  ├─ ChatMessageItem.vue
   │  └─ ChatInput.vue
   └─ composables/
      ├─ useChat.js
      ├─ useVoiceRecognition.js
      └─ useAudioPlayer.js
```