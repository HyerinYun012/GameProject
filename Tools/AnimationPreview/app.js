"use strict";

const CELL_SIZE = 256;
const ASSET_ROOT = window.SPRITE_ASSET_ROOT || "../../Assets/Sprites/Animals";
const DIRECTIONS = [
  { code: "S", label: "남쪽" },
  { code: "SE", label: "남동" },
  { code: "E", label: "동쪽" },
  { code: "NE", label: "북동" },
  { code: "N", label: "북쪽" },
  { code: "NW", label: "북서" },
  { code: "W", label: "서쪽" },
  { code: "SW", label: "남서" },
];

const ANIMATIONS = [
  {
    id: "bear",
    name: "곰",
    note: "무거운 보행과 앞발 휘두르기 공격",
    basePath: `${ASSET_ROOT}/Bear`,
    pivot: [128, 248],
    clips: [
      clip("idle", "대기", 4, 4, true),
      clip("walk", "걷기", 6, 6, true),
      clip("attack", "공격", 6, 10, false),
      clip("hurt", "피격", 3, 12, false),
      clip("death", "죽음", 6, 8, false),
    ],
  },
  {
    id: "wolf",
    name: "늑대",
    note: "빠른 보행과 전방 물기 공격",
    basePath: `${ASSET_ROOT}/Wolf`,
    pivot: [128, 248],
    clips: [
      clip("idle", "대기", 4, 4, true),
      clip("walk", "걷기", 6, 10, true),
      clip("attack", "공격", 6, 12, false),
      clip("hurt", "피격", 3, 12, false),
      clip("death", "죽음", 6, 8, false),
    ],
  },
  {
    id: "crow",
    name: "까마귀",
    note: "공중 대기와 이동용 비행, 공격 애니메이션 없음",
    basePath: `${ASSET_ROOT}/Crow`,
    pivot: [128, 128],
    clips: [
      clip("idle", "공중 대기", 4, 8, true),
      clip("walk", "비행 이동", 6, 12, true),
      clip("hurt", "피격", 3, 12, false),
      clip("death", "죽음", 6, 10, false),
    ],
  },
];

const state = {
  direction: 0,
  paused: false,
  speed: 1,
  cycleDirections: false,
  repeatOneShots: true,
  showGrid: true,
  lastTimestamp: performance.now(),
  directionElapsed: 0,
  cards: [],
  loaded: 0,
  failed: 0,
};

const elements = {
  sections: document.querySelector("#animal-sections"),
  template: document.querySelector("#animation-card-template"),
  directionButtons: document.querySelector("#direction-buttons"),
  currentDirection: document.querySelector("#current-direction"),
  playToggle: document.querySelector("#play-toggle"),
  restart: document.querySelector("#restart"),
  speed: document.querySelector("#speed"),
  speedOutput: document.querySelector("#speed-output"),
  cycleDirections: document.querySelector("#cycle-directions"),
  repeatOneShots: document.querySelector("#repeat-one-shots"),
  showGrid: document.querySelector("#show-grid"),
  loadStatus: document.querySelector("#load-status"),
};

function clip(id, name, frames, fps, loop) {
  return { id, name, frames, fps, loop };
}

function buildDirectionButtons() {
  DIRECTIONS.forEach((direction, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "direction-button";
    button.textContent = direction.code;
    button.title = direction.label;
    button.setAttribute("aria-pressed", String(index === state.direction));
    button.addEventListener("click", () => setDirection(index));
    elements.directionButtons.append(button);
  });
}

function buildSections() {
  ANIMATIONS.forEach((animal) => {
    const section = document.createElement("section");
    section.className = "animal-section";
    section.id = animal.id;

    const heading = document.createElement("header");
    heading.className = "section-heading";
    heading.innerHTML = `<h2>${animal.name}</h2><p>${animal.note}</p>`;

    const grid = document.createElement("div");
    grid.className = "animation-grid";

    animal.clips.forEach((animation) => {
      const card = createAnimationCard(animal, animation);
      grid.append(card.element);
      state.cards.push(card);
    });

    section.append(heading, grid);
    elements.sections.append(section);
  });
}

function createAnimationCard(animal, animation) {
  const fragment = elements.template.content.cloneNode(true);
  const element = fragment.querySelector(".animation-card");
  const canvas = fragment.querySelector(".sprite-stage");
  const context = canvas.getContext("2d");
  const stage = fragment.querySelector(".stage-wrap");
  const pivot = fragment.querySelector(".pivot-marker");
  const counter = fragment.querySelector(".frame-counter");
  const link = fragment.querySelector(".sheet-link");
  const image = new Image();
  const fileName = `${animal.id}_${animation.id}.png`;
  const source = `${animal.basePath}/${fileName}`;

  fragment.querySelector(".animation-kind").textContent = animal.id.toUpperCase();
  fragment.querySelector(".animation-name").textContent = animation.name;
  fragment.querySelector(".animation-meta").textContent =
    `${animation.frames}프레임 · ${animation.fps} FPS · ${animation.loop ? "반복" : "1회"}`;
  link.href = source;

  stage.classList.toggle("grid-visible", state.showGrid);
  pivot.style.left = `${(animal.pivot[0] / CELL_SIZE) * 100}%`;
  pivot.style.top = `${(animal.pivot[1] / CELL_SIZE) * 100}%`;

  const card = {
    element,
    canvas,
    context,
    stage,
    counter,
    image,
    animal,
    animation,
    elapsed: 0,
    frame: 0,
    ready: false,
    failed: false,
  };

  image.onload = () => {
    card.ready = true;
    state.loaded += 1;
    updateLoadStatus();
    drawCard(card);
  };
  image.onerror = () => {
    card.failed = true;
    state.failed += 1;
    updateLoadStatus();
    drawError(card, fileName, image.src);
  };
  image.src = source;

  return card;
}

function updateLoadStatus() {
  const total = state.cards.length;
  const finished = state.loaded + state.failed;
  if (finished < total) {
    elements.loadStatus.textContent = `스프라이트 불러오는 중 ${finished} / ${total}`;
    return;
  }
  if (state.failed) {
    elements.loadStatus.textContent =
      `${state.failed}개 시트를 불러오지 못했습니다. 프로젝트 루트의 AnimationPreview.html을 여세요.`;
    elements.loadStatus.className = "load-status error";
    return;
  }
  elements.loadStatus.textContent = `14개 시트 로드 완료 · ${state.cards.length}개 애니메이션 동시 재생`;
  elements.loadStatus.className = "load-status ready";
}

function setDirection(index) {
  state.direction = (index + DIRECTIONS.length) % DIRECTIONS.length;
  state.directionElapsed = 0;
  [...elements.directionButtons.children].forEach((button, buttonIndex) => {
    button.setAttribute("aria-pressed", String(buttonIndex === state.direction));
  });
  const direction = DIRECTIONS[state.direction];
  elements.currentDirection.textContent = `${direction.code} · ${direction.label}`;
  state.cards.forEach(drawCard);
}

function setPaused(paused) {
  state.paused = paused;
  elements.playToggle.textContent = paused ? "재생" : "일시정지";
  elements.playToggle.classList.toggle("button-primary", !paused);
}

function restartAll() {
  state.cards.forEach((card) => {
    card.elapsed = 0;
    card.frame = 0;
    drawCard(card);
  });
}

function updateCard(card, delta) {
  if (!card.ready) return;

  const { animation } = card;
  const frameDuration = 1000 / animation.fps;
  const animationDuration = animation.frames * frameDuration;
  const holdDuration = animation.loop ? 0 : 650;
  const repeat = animation.loop || state.repeatOneShots;

  card.elapsed += delta * state.speed;
  if (repeat) {
    const phase = card.elapsed % (animationDuration + holdDuration);
    card.frame = Math.min(animation.frames - 1, Math.floor(phase / frameDuration));
  } else {
    card.frame = Math.min(animation.frames - 1, Math.floor(card.elapsed / frameDuration));
  }
  drawCard(card);
}

function drawCard(card) {
  if (!card.ready) return;
  const sourceX = card.frame * CELL_SIZE;
  const sourceY = state.direction * CELL_SIZE;
  card.context.clearRect(0, 0, CELL_SIZE, CELL_SIZE);
  card.context.drawImage(
    card.image,
    sourceX,
    sourceY,
    CELL_SIZE,
    CELL_SIZE,
    0,
    0,
    CELL_SIZE,
    CELL_SIZE,
  );
  card.counter.textContent = `${card.frame + 1} / ${card.animation.frames}`;
}

function drawError(card, fileName, source) {
  card.context.clearRect(0, 0, CELL_SIZE, CELL_SIZE);
  card.context.fillStyle = "#ff9f8f";
  card.context.font = "600 13px sans-serif";
  card.context.textAlign = "center";
  card.context.fillText("로드 실패", CELL_SIZE / 2, CELL_SIZE / 2 - 8);
  card.context.fillStyle = "#9eaea5";
  card.context.font = "11px sans-serif";
  card.context.fillText(fileName, CELL_SIZE / 2, CELL_SIZE / 2 + 14);
  card.element.title = `로드 실패: ${source}`;
}

function animate(timestamp) {
  const delta = Math.min(100, timestamp - state.lastTimestamp);
  state.lastTimestamp = timestamp;

  if (!state.paused) {
    state.cards.forEach((card) => updateCard(card, delta));
    if (state.cycleDirections) {
      state.directionElapsed += delta * state.speed;
      if (state.directionElapsed >= 2400) {
        setDirection(state.direction + 1);
      }
    }
  }

  requestAnimationFrame(animate);
}

function bindControls() {
  elements.playToggle.addEventListener("click", () => setPaused(!state.paused));
  elements.restart.addEventListener("click", restartAll);
  elements.speed.addEventListener("input", () => {
    state.speed = Number(elements.speed.value);
    elements.speedOutput.value = `${state.speed.toFixed(2)}×`;
  });
  elements.cycleDirections.addEventListener("change", () => {
    state.cycleDirections = elements.cycleDirections.checked;
    state.directionElapsed = 0;
  });
  elements.repeatOneShots.addEventListener("change", () => {
    state.repeatOneShots = elements.repeatOneShots.checked;
    restartAll();
  });
  elements.showGrid.addEventListener("change", () => {
    state.showGrid = elements.showGrid.checked;
    state.cards.forEach((card) => card.stage.classList.toggle("grid-visible", state.showGrid));
  });

  window.addEventListener("keydown", (event) => {
    if (event.target instanceof HTMLInputElement) return;
    if (event.code === "Space") {
      event.preventDefault();
      setPaused(!state.paused);
    } else if (event.key.toLowerCase() === "r") {
      restartAll();
    } else if (event.key === "ArrowLeft") {
      setDirection(state.direction - 1);
    } else if (event.key === "ArrowRight") {
      setDirection(state.direction + 1);
    }
  });
}

buildDirectionButtons();
buildSections();
bindControls();
setDirection(0);
requestAnimationFrame(animate);
