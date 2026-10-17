
from winotify import Notification

notification = Notification(
    app_id="StudyFlow",
    title="StudyFlow Test",
    msg="Great! Your Windows desktop notifications are working.",
    duration="short"
)

notification.show()
