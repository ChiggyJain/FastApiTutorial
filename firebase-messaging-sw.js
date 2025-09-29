
// Import scripts for firebase in service worker context (compact for messaging)
importScripts('https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.23.0/firebase-messaging-compat.js');

// ---------- CONFIG: SAME AS IN index.html ----------
const firebaseConfig = {
    apiKey: "AIzaSyB_JO4U2Eb5Uuf0sRPWkD81cX9-9vJzHsU",
    authDomain: "cj-fastapi-push-ntf.firebaseapp.com",
    projectId: "cj-fastapi-push-ntf",
    storageBucket: "cj-fastapi-push-ntf.firebasestorage.app",
    messagingSenderId: "891797103531",
    appId: "1:891797103531:web:bceec7e05fb9d49058e8ee",
    measurementId: "G-WZ5D71NXV4"
};

firebase.initializeApp(firebaseConfig);

const messaging = firebase.messaging();

// Background message handler
messaging.onBackgroundMessage(function(payload) {
  console.log('[firebase-messaging-sw.js] Received background message ', payload);
  const notificationTitle = payload.notification?.title || 'Background Message Title';
  const notificationOptions = {
    body: payload.notification?.body || '',
    icon: '/static/icon.png',
    data: {
      click_action: payload.data?.click_action || payload.notification?.click_action || 'https://coderarmy.in/'
    }
  };
  self.registration.showNotification(notificationTitle, notificationOptions);
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data.click_action)
  );
});


