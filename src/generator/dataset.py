"""Generator module to create 200 realistic, constrained CTU student records."""

import json
import random
from pathlib import Path

from src.parser.models import StudentRecord

# Constants from Government & CTU guidelines
PROVINCES_34: list[str] = [
    # 6 Centrally-governed cities
    "Cần Thơ", "Hồ Chí Minh", "Hà Nội", "Hải Phòng", "Đà Nẵng", "Huế",
    # 28 Provinces after reorganization
    "An Giang", "Cà Mau", "Đồng Tháp", "Vĩnh Long", "Đồng Nai", "Tây Ninh",
    "Lâm Đồng", "Đắk Lắk", "Gia Lai", "Khánh Hoà", "Quảng Ngãi", "Quảng Trị",
    "Ninh Bình", "Hưng Yên", "Bắc Ninh", "Phú Thọ", "Thái Nguyên", "Lào Cai",
    "Cao Bằng", "Điện Biên", "Hà Tĩnh", "Lai Châu", "Lạng Sơn", "Nghệ An",
    "Quảng Ninh", "Thanh Hóa", "Sơn La", "Bến Tre",
]

# Weights for provinces (biased towards Mekong Delta & South)
PROVINCE_WEIGHTS: list[float] = [
    30.0, 10.0, 1.0, 1.0, 2.0, 1.0,  # Cities
    15.0, 10.0, 10.0, 10.0, 3.0, 2.0,  # SW provinces
    1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
    1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
    1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
    1.0, 1.0, 1.0, 1.0,
]

MAJORS_CTU: list[str] = [
    "Kinh tế",
    "Quản trị kinh doanh",
    "Marketing",
    "Kinh doanh quốc tế",
    "Tài chính - Ngân hàng",
    "Kế toán",
    "Thương mại điện tử",
    "Logistics và Quản lý chuỗi cung ứng",
    "Công nghệ thông tin",
    "Khoa học máy tính",
    "Kỹ thuật phần mềm",
    "Hệ thống thông tin",
    "Mạng máy tính và truyền thông dữ liệu",
    "Trí tuệ nhân tạo",
    "Kỹ thuật điện",
    "Kỹ thuật cơ điện tử",
    "Công nghệ sinh học",
    "Công nghệ thực phẩm",
    "Bảo vệ thực vật",
    "Nuôi trồng thủy sản",
    "Thú y",
    "Ngôn ngữ Anh",
    "Ngôn ngữ Pháp",
    "Luật",
    "Du lịch",
    "Báo chí",
    "Truyền thông đa phương tiện",
]

LAST_NAMES = ["Nguyễn", "Trần", "Lê", "Phạm", "Huỳnh", "Hoàng", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"]
MID_NAMES_MALE = ["Văn", "Hữu", "Đức", "Thành", "Quốc", "Minh", "Hoàng", "Tuấn", "Thanh", "Trọng", "Đình"]
FIRST_NAMES_MALE = ["Nam", "Khang", "Phúc", "Bảo", "Khánh", "Thịnh", "Huy", "Duy", "Phát", "Tài", "Đạt", "Lộc", "Kiệt", "Khoa"]

MID_NAMES_FEMALE = ["Thị", "Ngọc", "Thanh", "Kim", "Mỹ", "Phương", "Ái", "Tuyết", "Mai", "Thảo", "Hồng"]
FIRST_NAMES_FEMALE = ["Anh", "Vy", "Trang", "Linh", "Hân", "Nhi", "Ngân", "Duyên", "Trúc", "Châu", "Thy", "Quyên", "Mai", "Tiên"]

KHMER_NAMES = [
    ("Thạch", "Minh Sơn", "Nam"), ("Thạch", "Thị Sô Phia", "Nữ"),
    ("Chau", "Sóc Kha", "Nam"), ("Chau", "Thị Som Nang", "Nữ"),
    ("Sơn", "Văn Đô", "Nam"), ("Kim", "Thị Ngọc Giàu", "Nữ"),
    ("Danh", "Hoàng Quân", "Nam"), ("Danh", "Thị Chanh Đa", "Nữ"),
]

HOA_NAMES = [
    ("Lâm", "Vĩnh Phát", "Nam"), ("Lâm", "Mỹ Linh", "Nữ"),
    ("Lưu", "Gia Lạc", "Nam"), ("Lưu", "Thục Quyên", "Nữ"),
    ("Trịnh", "Quốc Hào", "Nam"), ("Hứa", "Kim Ngân", "Nữ"),
]

LIKERT_ENTRY_IDS = [
    # 1. Gia san pham
    "367715589", "1793328063", "1337519800",
    # 2. Thu nhap
    "1030502833", "177287632", "358871458",
    # 3. Khuyen mai
    "1089747739", "547226249", "1374128538",
    # 4. Phi van chuyen
    "1047777526", "270245976", "1441213877",
    # 5. Danh gia
    "134724748", "2054430395", "954541224", "569463304",
    # 6. Livestream
    "1186068398", "1327855885", "1860421887",
    # 7. KOL/KOC
    "1687227123", "1913589656", "255915353",
    # 8. Xu huong
    "760325758", "212279939", "529176916",
    # 9. Tien loi & niem tin
    "1595323384", "422015240", "1154756447",
    # P3: Quyet dinh mua sam
    "219384669", "1261613827", "753938464",
]


def generate_vietnamese_name(gender: str, ethnicity: str) -> str:
    """Generate authentic Vietnamese name matching gender and ethnicity."""
    if ethnicity == "Khmer":
        last, rest, _ = random.choice(KHMER_NAMES)
        return f"{last} {rest}"
    if ethnicity == "Hoa":
        last, rest, _ = random.choice(HOA_NAMES)
        return f"{last} {rest}"

    last = random.choice(LAST_NAMES)
    if gender == "Nam":
        mid = random.choice(MID_NAMES_MALE)
        first = random.choice(FIRST_NAMES_MALE)
    else:
        mid = random.choice(MID_NAMES_FEMALE)
        first = random.choice(FIRST_NAMES_FEMALE)
    return f"{last} {mid} {first}"


def generate_dataset(count: int = 200, output_path: Path | None = None) -> list[StudentRecord]:
    """Generate unique constrained student records."""
    records: list[StudentRecord] = []
    used_mssvs: set[str] = {"B2306882"}  # Exclude author MSSV

    # Cohort distribution: K49 (70%), K50 (15%), K51 (10%), K48 (5%)
    cohort_choices = ["K49"] * 70 + ["K50"] * 15 + ["K51"] * 10 + ["K48"] * 5
    cohort_prefix_map = {
        "K48": ("B22", 2004, [2004, 2003, 2002]),
        "K49": ("B23", 2005, [2005, 2004, 2003]),
        "K50": ("B24", 2006, [2006, 2005, 2004]),
        "K51": ("B25", 2007, [2007, 2006, 2005]),
    }

    spending_choices = ["Dưới 2tr", "Từ 2tr - 4tr", "Từ 4tr - 6tr", "Từ 6tr trở lên"]
    spending_weights = [25.0, 50.0, 20.0, 5.0]

    ethnicity_choices = ["Kinh", "Khmer", "Hoa"]
    ethnicity_weights = [88.0, 9.0, 3.0]

    for _ in range(count):
        cohort = random.choice(cohort_choices)
        prefix, default_year, year_pool = cohort_prefix_map[cohort]

        # Generate unique MSSV: B + 2 digits + 5 digits in 00000..08000
        while True:
            num = random.randint(0, 8000)
            mssv = f"{prefix}{num:05d}"
            if mssv not in used_mssvs:
                used_mssvs.add(mssv)
                break

        # Birth year distribution: 85% default year, 15% +-1 year
        if random.random() < 0.85:
            birth_year = default_year
        else:
            birth_year = random.choice(year_pool)

        gender = "Nam" if random.random() < 0.45 else "Nữ"
        ethnicity = random.choices(ethnicity_choices, weights=ethnicity_weights, k=1)[0]
        full_name = generate_vietnamese_name(gender, ethnicity)
        major = random.choice(MAJORS_CTU)
        major_cohort = f"{major} - {cohort}"

        hometown = random.choices(PROVINCES_34, weights=PROVINCE_WEIGHTS, k=1)[0]
        spending = random.choices(spending_choices, weights=spending_weights, k=1)[0]

        # Ratings 1..5 with realistic distribution for satisfied TikTok Shop shoppers
        # Score 3: 20%, Score 4: 55%, Score 5: 20%, Score 1-2: 5%
        ratings = {}
        for entry_id in LIKERT_ENTRY_IDS:
            score = random.choices([1, 2, 3, 4, 5], weights=[2.0, 3.0, 20.0, 55.0, 20.0], k=1)[0]
            ratings[entry_id] = score

        record = StudentRecord(
            full_name=full_name,
            gender=gender,
            mssv=mssv,
            major_cohort=major_cohort,
            birth_year=birth_year,
            hometown=hometown,
            ethnicity=ethnicity,
            used_tiktok_shop="Đã từng",
            monthly_spending=spending,
            ratings=ratings,
        )
        records.append(record)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([r.model_dump() for r in records], f, ensure_ascii=False, indent=2)

    return records


if __name__ == "__main__":
    generate_dataset(200, Path("data/samples/ctu_survey_200.json"))
    print("Generated 200 records in data/samples/ctu_survey_200.json")
