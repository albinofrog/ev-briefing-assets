# EV 브리핑 채팅 반영 절차 (chat_ops.md)

예약 작업 프롬프트 바절이 가리키는 절차입니다. 예약 실행에서는 읽지도 하지도 않습니다. 이 파일을 바꾸는 것은 layer `prompt` 개선안과 같게 다룹니다.

사용자가 채팅에서 보드 승인분 반영이나 통합을 요청하면, 그 채팅 세션이 저장소를 연결해 다음을 합니다.
1. 메모리 `patches.md`의 수정(이미 회차에 적용 중)을 저장소 파일에 같은 문구로 넣고, 보드 proposals에서 `status: needs_chat`인 개선안은 change대로 고칩니다. rules.md를 고쳤으면 `build.py guard <고치기 전> <고친 뒤>` 종료 0, 그다음 `EV_W=/tmp/evgate python3 eval/score.py` 종료 0이어야 합니다. build.py를 고쳤으면 `python3 eval/test_patch.py`와 `python3 eval/test_review.py`도 종료 0이어야 합니다. 통과하면 `apply(p번호): 제목`으로 main에 커밋·푸시하고, rules.md·improve.md·build.py 가운데 하나라도 바꿨으면 메모리 `config.md`의 `ref`를 새 커밋으로 바꿉니다. layer `prompt`는 예약 작업 프롬프트와 저장소 `prompt.md`를 같은 문구로 고치고, 고친 뒤 두 전문이 같은지 대조합니다. rules.md·improve.md를 바꾸는 개선안은 고치기 전·후 문구를 사용자에게 보여 확인받은 뒤 커밋합니다. rules.md 2~6절을 바꾸면 그 전에 `eval/replay.md` 절차로 개정 전·후 판정 점수를 비교해 함께 보여 줍니다. 통합한 수정은 메모리 `patches.md`에서 지웁니다.
   build.py의 scorecard 지표 계산을 바꿨으면 메모리 `run_log.md`에 `지표 계산 변경: <바뀐 지표> <커밋> <날짜>` 한 줄을 append합니다.
2. 반영한 개선안은 보드 `status: applied`, 메모리 `lessons.md`의 교훈 상태를 반영으로 바꾸고 관찰 지표 칸에 `반영 <metrics.md 줄 수>`를 덧붙입니다. 실패하면 되돌리고 `status: failed`, `apply_error: 사유 한 줄`.
3. 사용자가 채팅에서 이 예약 작업의 수동 실행을 요청하면, 정식 회차로 낼 것인지 먼저 확인합니다. 확인용이면 메모리 `config.md`를 `dry: on`으로 바꾼 뒤 실행하고, 실행이 끝나면 `dry: off`로 되돌립니다(수동 확인 실행이 호 번호·장부·metrics.md를 움직이지 않게).
