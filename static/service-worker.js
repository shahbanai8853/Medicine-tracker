```javascript
self.addEventListener('push', function(event) {
    let data = {};
    if (event.data) {
        try { data = event.data.json(); } 
        catch (e) { data = { title: 'Medicine Tracker', body: event.data.text() }; }
    } else {
        data = { title: 'Medicine Alert', body: 'your medicine will empty Tomorrow' };
    }
    const options = {
        body: data.body,
        vibrate: [200, 100, 200],
        data: { dateOfArrival: Date.now(), primaryKey: '1' }
    };
    event.waitUntil(self.registration.showNotification(data.title, options));
});
