# 동물 애니메이션 검수 도구

프로젝트 루트의 `OpenAnimationPreview.cmd`를 더블클릭하면 로컬 서버와 브라우저가 자동으로 열립니다. 곰, 늑대, 까마귀의 모든 애니메이션을 동시에 확인할 수 있습니다.

브라우저 보안 정책 때문에 `AnimationPreview.html`을 파일로 직접 열면 PNG 로드가 차단될 수 있습니다. 반드시 `OpenAnimationPreview.cmd`를 사용하세요. 실행 중 나타나는 콘솔 창을 닫거나 `Ctrl+C`를 누르면 서버가 종료됩니다.

## 기능

- 14개 애니메이션 동시 재생
- 8방향 수동 전환 및 자동 순환
- 재생/정지, 처음부터 재생, 0.25~2배속
- 공격, 피격, 죽음 같은 1회 동작의 반복 검수
- 셀 경계와 피벗 위치 확인

직접 실행하려면 프로젝트 루트에서 아래 명령을 실행한 뒤 표시되는 주소에 접속합니다.

```powershell
python Tools/AnimationPreview/serve_preview.py
```
