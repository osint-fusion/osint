import re
import ipaddress

class TargetValidator:
    USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_\-\.]{1,64}$')
    DOMAIN_REGEX = re.compile(r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}$')

    @classmethod
    def validate(cls, target_type: str, target_value: str) -> tuple[bool, str]:
        target_value = target_value.strip()
        if not target_value:
            return False, "قيمة الهدف فارغة"

        if target_type == "username":
            if cls.USERNAME_REGEX.match(target_value):
                return True, target_value
            return False, "اسم المستخدم غير صالح"

        elif target_type == "domain":
            clean_domain = target_value.lower().replace("http://", "").replace("https://", "").split("/")[0]
            if cls.DOMAIN_REGEX.match(clean_domain):
                return True, clean_domain
            return False, "اسم الدومين غير صالح"

        elif target_type == "ip":
            try:
                ip_obj = ipaddress.ip_address(target_value)
                if ip_obj.is_private or ip_obj.is_loopback:
                    return False, "عنوان IP خاص غير مسموح بالاستعلام عنه"
                return True, str(ip_obj)
            except ValueError:
                return False, "عنوان IP غير صحيح"

        elif target_type in ["email", "phone"]:
            return True, target_value

        return False, "نوع الهدف غير مدعوم"
