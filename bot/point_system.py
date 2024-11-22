class PointSystem:
    @staticmethod
    def calculate_points(amount):
        return int(amount / 10000)  # هر 10 هزار تومان 1 امتیاز

    @staticmethod
    def calculate_discount(points):
        return points * 1000  # هر امتیاز 1000 تومان تخفیف
