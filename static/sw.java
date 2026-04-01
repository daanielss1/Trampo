self.addEventListener("install", event => {
  console.log("Service Worker instalado");
});

self.addEventListener("push", function(event) {
  const data = event.data.text();

  self.registration.showNotification("Nova vaga 🚀", {
    body: data,
    icon: "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
  });
});