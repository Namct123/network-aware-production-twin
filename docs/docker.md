# Docker cho lõi Digital Twin

Docker hiện đóng gói **lõi DT + MuJoCo không cửa sổ**, gồm estimator, mạng giả lập,
sequence, predictor, supervisor, cấu hình và các bộ kiểm tra. Viewer, CAD/Fusion,
Unity và kết nối PLC thật nằm ngoài hạng mục này. Mặc định candidate mới dùng plant chức năng theo kích thước sơ bộ; baseline cũ vẫn được giữ.

## 1. Chạy trên máy hiện tại từ PowerShell

**Trạng thái 30/10/2026:** bản lõi đầu đã được người dùng chấp thuận với tag
`accepted-20261030-core-v1`. Hạng mục thông số/cơ học ở
`candidate-20261030-parameters` và hạng mục bộ ước lượng/giám sát tín hiệu mới ở
`candidate-20261030-observer-health` đều chờ người dùng kiểm nghiệm.
Hạng mục tiếp theo là `candidate-20261030-reconfiguration`, cũng chờ kiểm nghiệm.
Ngày 31/10 bổ sung `candidate-20261031-robustness`, cũng chờ kiểm nghiệm.
Hạng mục tiếp theo là `candidate-20261031-adaptive-speed`, cũng chờ kiểm nghiệm.
Wrapper hiện chọn `candidate-20261103-background-observer`, cũng chờ kiểm nghiệm; demo
mặc định vẫn dùng cap cố định. [Adaptive-check](adaptive_speed.md) và
[recovery-check](hold_recovery.md) dùng profile thử riêng, không tự áp vào mọi lượt.
Chế độ `reset-check` thử [gửi yêu cầu đặt lại và bắt đầu lượt mô phỏng mới](dat_lai_chu_trinh_moi.md).
Chi tiết: [hồ sơ phiên bản](../docker/RELEASES.md).

Ngày 03/11 bổ sung [MuJoCo nền chỉ quan sát](du_bao_nen_quan_sat.md).
Chạy `./scripts/docker_dt.ps1 -Mode background-check` để thử ba chu trình đối chứng.
Chế độ này tự giữ nhịp gần thời gian trên máy và cần khoảng một phút trở lên tùy máy.
Không áp lệnh từ kết quả nền; demo thông thường vẫn dùng nhánh 1D.

Mở terminal tại thư mục dự án:

```powershell
./scripts/docker_dt.ps1 -Mode build
./scripts/docker_dt.ps1 -Mode demo
./scripts/docker_dt.ps1 -Mode fault
./scripts/docker_dt.ps1 -Mode strict
./scripts/docker_dt.ps1 -Mode tests
./scripts/docker_dt.ps1 -Mode acceptance
./scripts/docker_dt.ps1 -Mode predictive-check
./scripts/docker_dt.ps1 -Mode measured-check
./scripts/docker_dt.ps1 -Mode observer-check
./scripts/docker_dt.ps1 -Mode reconfiguration-check
./scripts/docker_dt.ps1 -Mode robustness-check -Plan robustness_smoke.json
./scripts/docker_dt.ps1 -Mode robustness-check
./scripts/docker_dt.ps1 -Mode adaptive-check -Plan adaptive_speed_smoke.json
./scripts/docker_dt.ps1 -Mode adaptive-check
./scripts/docker_dt.ps1 -Mode recovery-check
./scripts/docker_dt.ps1 -Mode reset-check
```

`build` dựng image, những lệnh còn lại tạo container ngắn hạn rồi tự xóa container
khi kết thúc. Dữ liệu không bị xóa: mỗi lượt nằm riêng ở `output/docker/` trên máy.
`demo` phải DONE và placement=true; `fault`/`strict` chủ đích HOLD có lý do.
Chạy không giao diện nên sẽ không mở cửa sổ robot. Không cần GPU.

Máy này dùng Docker Engine trong WSL `Ubuntu-24.04`; wrapper chọn Docker Windows
nếu có, nếu không gọi engine WSL bằng root. Trong container, chương trình chạy
với UID 10001, không chạy root. Không bật mạng, không mở cổng ra ngoài.

## 2. Đổi thông số, không sửa lõi

Sao chép profile vào `mujoco/configs/`, chỉnh đơn vị SI và chạy:

```powershell
./scripts/docker_dt.ps1 -Mode demo -Config predictive_demo.json -Bin 3
```

Profile được gắn chỉ đọc từ máy vào `/profiles`. Không nhập hồ sơ survey trực tiếp
vào `--config`: survey và machine profile là hai định dạng khác nhau.
Không truyền `-Config` thì demo của candidate mới dùng `reconfigurable_cell_20261030.json` đã đóng trong image;
các bộ kiểm tra dùng profile mặc định riêng như mã nguồn. Mỗi lượt lưu cấu hình hiệu
lực và manifest; xem `summary.json`, `results.json`, `comparison.json` theo loại lượt.

## 3. Máy khác có Docker

Giữ cây mã nguồn có Dockerfile, compose.yaml, mujoco, bảng parts.csv và launcher.
Không dùng ZIP cũ ngày 29/10 để giả định có Dockerfile mới. Trong thư mục gốc:

```bash
python3 docker/build_image.py
docker compose run --rm dt demo
docker compose run --rm dt fault
docker compose run --rm dt predictive-check
docker compose run --rm --entrypoint python dt -m unittest discover -s mujoco -p 'test_*.py'
```

Linux dùng Docker Engine; Windows có thể dùng Docker Desktop Linux containers.
Nếu dùng Docker Engine trong WSL như máy này, chạy lệnh trong WSL với `sudo`.
Không cài song song hai engine vào cùng một môi trường khi chưa kiểm tra cấu hình.
Lần build đầu cần Internet để lấy image Python và gói. Container thí nghiệm chạy offline.
Builder gửi tar chỉ gồm danh sách tệp runtime được phép, không quét cache/.git/tài liệu
cá nhân. Đây cũng là cách tránh lỗi xattr khi build trực tiếp từ thư mục NTFS trong WSL.
Compose dùng image đã build; không dùng `docker compose build` cho dự án này.
Nếu bind mount đầu ra trên Linux không ghi được, tạo thư mục và cấp quyền cho UID
10001 hoặc chạy `docker compose run --rm --user "$(id -u):$(id -g)" dt demo`.

Muốn chuyển image đã build mà không push registry:

```bash
docker image save -o dt-candidate.tar production-twin-dt:candidate-20261031-reset-protocol
# Máy nhận: docker image load -i dt-candidate.tar
```

## 4. Quy tắc nghiệm thu từ nay

1. Hoàn thành một hạng mục, kiểm tra tự động và dựng image `candidate`.
2. Cung cấp lệnh, dữ liệu và tiêu chí để **bạn kiểm nghiệm**.
3. Khi bạn xác nhận đạt, cập nhật hạng mục vào bản Docker được chấp thuận ngay,
   ghi nội dung xác nhận, image ID, hash mã nguồn và bằng chứng trong `docker/RELEASES.md`.
4. Giữ bản đã chấp thuận cũ để quay lại khi cần; không tự suy diễn kiểm tra PASS
   thành bạn đã chấp thuận. Lệnh build không tự tạo tag stable/latest/accepted.

Mỗi hạng mục tiếp theo dùng tag candidate mới để không ghi đè snapshot đang được bạn
kiểm nghiệm, ví dụ `./scripts/docker_dt.ps1 -Mode build -Tag candidate-20261101`.
Khi chạy kiểm tra tag đó, truyền cùng `-Tag candidate-20261101`. Tag được truyền
tường minh vào cả Docker Windows và engine WSL; không phụ thuộc biến môi trường
Windows có tự đi qua WSL hay không.

`source_manifest.json` bên trong image ghi đúng mã và phiên bản thư viện đã đóng gói:

```powershell
./scripts/docker_dt.ps1 -Mode manifest
```

Đổi mã trên máy không tự đổi mã bên trong image: cần build lại. Profile gắn ngoài
có thể khác profile đã đóng gói, vì vậy kết quả phải đi cùng effective_config/manifest.
Docker không bảo đảm timing/bitwise giống tuyệt đối giữa CPU khác nhau. Ngưỡng
wall-clock của predictor vẫn có thể bị ảnh hưởng bởi tải hệ thống.
Image Python nền được khóa bằng digest; các gói Python trực tiếp và gián tiếp được
khóa tại `docker/requirements.lock`. Gói hệ điều hành có thể thay đổi khi build lại
từ kho apt, nên muốn chuyển đúng môi trường đã nghiệm thu thì lưu/chuyển image ID
đó, không chỉ build lại từ Dockerfile. Trạng thái nghiệm thu mới nhất nằm ở
`docker/RELEASES.md`; metadata trong image chỉ ghi trạng thái lúc build.

## 5. Cài engine WSL khi chuyển máy (tùy chọn)

Chỉ dành cho Ubuntu WSL chưa có Docker, xem script trước khi chạy:

```bash
sudo bash docker/install_wsl_engine.sh
```

Script thêm kho apt có chữ ký chính thức và cài Engine/Compose; không tự gỡ các
gói xung đột. Người dùng Docker Desktop bỏ qua bước này.

Nguồn kỹ thuật: https://docs.docker.com/engine/install/ubuntu/
và https://docs.docker.com/build/building/best-practices/ .

## Plant theo số đo và nhập thông số

Xem [hướng dẫn 194 trường số, CSV và phân biệt giả định/số đo](parameterized_core.md).
Bản accepted cũ vẫn chạy bằng `./scripts/docker_dt.ps1 -Mode demo -Tag accepted-20261030-core-v1`.
Không coi kết quả của hai hình học khác nhau là phép so sánh tăng tốc trực tiếp.
