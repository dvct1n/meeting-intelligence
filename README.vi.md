# 🎙️ AI Meeting Intelligence

Hệ thống biến bản ghi âm cuộc họp dài thành **tri thức có cấu trúc và tìm kiếm được**: ai nói gì, quyết định gì, ai phụ trách việc nào và hạn khi nào, kèm tìm kiếm ngữ nghĩa trên toàn bộ các cuộc họp cũ. Hỗ trợ tiếng Việt và các ngôn ngữ Whisper hỗ trợ.

[English](README.md) · [GitHub](https://github.com/dvct1n/meeting-intelligence) · [Báo cáo mẫu](examples/sample_report.md) (dữ liệu giả lập)

## Pipeline

`audio/video` → ffmpeg (16 kHz mono) → **Whisper** (nhận dạng giọng nói) + **pyannote** (phân tách người nói) → ghép người nói theo độ chồng lấp → chia đoạn theo chủ đề (embedding) → **LLM** (tóm tắt, quyết định, action item có người phụ trách/deadline, tóm tắt theo từng người nói) → embedding đa ngôn ngữ → **Qdrant** → **FastAPI / CLI / Streamlit**.

## Cài đặt nhanh

Yêu cầu: Python 3.10+, `ffmpeg` (nên có GPU).

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[all]"
cp .env.example .env          # cấu hình LLM; HF_TOKEN chỉ cần khi bật diarization
```

- **Diarization:** cần chấp nhận điều khoản của `pyannote/speaker-diarization-3.1` và `pyannote/segmentation-3.0` trên Hugging Face, rồi đặt `HF_TOKEN`. Không có token thì đặt `DIARIZE=false`.
- **LLM:** OpenAI, model chạy local qua Ollama (`LLM_BASE_URL=http://localhost:11434/v1`) hoặc Anthropic (`LLM_PROVIDER=anthropic`).

```bash
meeting-intel process hop.mp3 -o bao-cao.md      # xử lý và xuất báo cáo Markdown
meeting-intel search "đã quyết định gì về ngày phát hành?"

uvicorn meeting_intel.api:app --reload           # API  → http://localhost:8000/docs
streamlit run ui/streamlit_app.py                # giao diện → http://localhost:8501
```

Docker: `docker compose up --build`.

Chỉ muốn chạy test? `pip install -e ".[dev]" && make check` — không cần tải model vì test dùng đối tượng giả.

## Demo offline không cần audio hoặc API key

Cài dependencies nhẹ bằng `pip install -e ".[dev]"`, sau đó chạy:

```bash
make demo
# hoặc: python scripts/run_demo.py
```

Demo sẽ validate meeting mẫu bằng schema, hiển thị summary/decisions/action items đã có sẵn, tìm kiếm từ khóa trên transcript và xuất `artifacts/demo-report.md`. Đây là walkthrough dựa trên dữ liệu giả lập, **không chạy pipeline suy luận ML**: không gọi Whisper, pyannote, LLM, neural embedding hoặc Qdrant.

Để xem các hàm metric hoạt động, chạy `make synthetic-eval`. Các fixture transcript/action item và thứ hạng tìm kiếm đều được viết thủ công; kết quả chỉ minh họa cách tính metric, không phải kết quả đánh giá model thực tế. Xử lý audio thật cần recording được phép sử dụng, cài ML dependencies và cấu hình LLM / Hugging Face khi cần.

## Quyền riêng tư và bảo mật

Âm thanh, transcript và vector được lưu trong `DATA_DIR`; nội dung transcript được gửi tới nhà cung cấp LLM mà bạn cấu hình (dùng model local để giữ dữ liệu meeting trong hạ tầng của bạn). Hãy bảo đảm người tham gia đồng ý việc ghi âm. API **không bật xác thực nếu chưa cấu hình `API_KEY`**, đồng thời chưa có tài khoản người dùng hoặc phân quyền theo từng meeting. Docker Compose mặc định chỉ bind port vào localhost. Không đưa `.env`, API key, token, audio/video hoặc transcript riêng tư lên GitHub. Docker Compose dùng named volume để lưu dữ liệu, chạy non-root và chỉ mở port trên localhost. Xem [checklist public/release](docs/github_release_checklist.md) và [security policy](SECURITY.md) trước khi push.

## Giới hạn

Giọng nói chồng lấp chỉ gán cho một người; nhãn người nói ẩn danh (`Speaker 1…`); mỗi lần chỉ xử lý một bản ghi; chưa có hàng đợi công việc.

Hiện repo **chưa có kết quả benchmark trên dữ liệu meeting thật**. Xem [quy trình đánh giá](docs/evaluation.md), [tái lập môi trường](docs/reproducibility.md), [checklist public/release](docs/github_release_checklist.md), [kiến trúc](docs/architecture.md) và [đóng góp](CONTRIBUTING.md). Giấy phép [MIT](LICENSE).
