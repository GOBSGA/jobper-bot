// Jobper Service Worker — Push Notifications
self.addEventListener("push", (e) => {
  const data = e.data?.json() || {};
  e.waitUntil(
    self.registration.showNotification(data.title || "Jobper", {
      body: data.body || "",
      icon: "/favicon.ico",
      badge: "/favicon.ico",
      data: { url: data.url || "/" },
    })
  );
});

self.addEventListener("notificationclick", (e) => {
  e.notification.close();
  const url = e.notification.data?.url || "/";
  e.waitUntil(clients.openWindow(url));
});
