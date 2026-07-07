from __future__ import annotations

import json
import math
import random
import tkinter as tk
from dataclasses import dataclass, field
from tkinter import filedialog, messagebox, ttk


WIDTH = 1040
HEIGHT = 700
PANEL_WIDTH = 340
CANVAS_WIDTH = WIDTH - PANEL_WIDTH
CANVAS_HEIGHT = HEIGHT

PROTON = "proton"
NEUTRON = "neutron"
ELECTRON = "electron"
SPIN_AUTO = "auto"
SPIN_UP = 1
SPIN_DOWN = -1

PARTICLE_RADIUS = 8
ELECTRON_RADIUS = 5
MAX_PARTICLES = 160
MAX_SPEED = 15.0
MAX_FORCE = 8.0
MIN_DISTANCE = 8.0

FONT = "Malgun Gothic"
BG = "#101214"
GRID = "#22282d"
PANEL_BG = "#f4f2ed"
TEXT = "#191b1f"
MUTED = "#60646c"
PROTON_FILL = "#e84855"
PROTON_OUTLINE = "#ffb3ba"
NEUTRON_FILL = "#35a7b8"
NEUTRON_OUTLINE = "#b7edf2"
ELECTRON_FILL = "#f2c14e"
ELECTRON_OUTLINE = "#fff1a8"
BOND = "#f2c14e"
PAULI_LINE = "#b06cff"
VELOCITY = "#f7f7f2"
TRAIL_PROTON = "#7e2d35"
TRAIL_NEUTRON = "#246b75"
TRAIL_ELECTRON = "#8a6d1d"
SPIN_UP_COLOR = "#fff0a8"
SPIN_DOWN_COLOR = "#d8c7ff"

KIND_KO = {
    PROTON: "양성자",
    NEUTRON: "중성자",
    ELECTRON: "전자",
}


@dataclass
class Particle:
    kind: str
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    mass: float = 1.0
    spin: int = SPIN_UP
    trail: list[tuple[float, float]] = field(default_factory=list)

    @property
    def charge(self) -> float:
        if self.kind == PROTON:
            return 1.0
        if self.kind == ELECTRON:
            return -1.0
        return 0.0

    @property
    def radius(self) -> int:
        return ELECTRON_RADIUS if self.kind == ELECTRON else PARTICLE_RADIUS

    @property
    def fill(self) -> str:
        if self.kind == PROTON:
            return PROTON_FILL
        if self.kind == ELECTRON:
            return ELECTRON_FILL
        return NEUTRON_FILL

    @property
    def outline(self) -> str:
        if self.kind == PROTON:
            return PROTON_OUTLINE
        if self.kind == ELECTRON:
            return ELECTRON_OUTLINE
        return NEUTRON_OUTLINE

    @property
    def spin_symbol(self) -> str:
        return "↑" if self.spin == SPIN_UP else "↓"

    @property
    def spin_color(self) -> str:
        return SPIN_UP_COLOR if self.spin == SPIN_UP else SPIN_DOWN_COLOR

    @property
    def label(self) -> str:
        if self.kind == PROTON:
            base = "p+"
        elif self.kind == ELECTRON:
            base = "e-"
        else:
            base = "n0"
        return f"{base}{self.spin_symbol}"

    @property
    def korean_name(self) -> str:
        return KIND_KO.get(self.kind, self.kind)


@dataclass
class DecayFlash:
    x: float
    y: float
    vx: float
    vy: float
    label: str
    color: str
    life: int = 42
    max_life: int = 42


class NucleonSimulator:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("핵자 샌드박스")
        self.root.geometry(f"{WIDTH}x{HEIGHT}")
        self.root.minsize(880, 560)

        self.particles: list[Particle] = []
        self.flashes: list[DecayFlash] = []
        self.running = True
        self.dragged_index: int | None = None
        self.drag_previous: tuple[float, float] | None = None
        self.selected_index: int | None = None
        self.selected_kind = tk.StringVar(value=PROTON)
        self.selected_spin = tk.StringVar(value=SPIN_AUTO)

        self.strong_enabled = tk.BooleanVar(value=True)
        self.electric_enabled = tk.BooleanVar(value=True)
        self.pauli_enabled = tk.BooleanVar(value=True)
        self.beta_enabled = tk.BooleanVar(value=False)
        self.beta_balance_enabled = tk.BooleanVar(value=True)
        self.fusion_enabled = tk.BooleanVar(value=True)
        self.fission_enabled = tk.BooleanVar(value=True)
        self.trails_enabled = tk.BooleanVar(value=True)
        self.labels_enabled = tk.BooleanVar(value=True)
        self.spin_labels_enabled = tk.BooleanVar(value=True)
        self.bonds_enabled = tk.BooleanVar(value=True)
        self.mo_orbitals_enabled = tk.BooleanVar(value=True)
        self.velocity_enabled = tk.BooleanVar(value=False)
        self.flashes_enabled = tk.BooleanVar(value=True)

        self.strong_strength = tk.DoubleVar(value=1.5)
        self.core_strength = tk.DoubleVar(value=1.2)
        self.electric_strength = tk.DoubleVar(value=85.0)
        self.pauli_strength = tk.DoubleVar(value=2.0)
        self.strong_range = tk.DoubleVar(value=45.0)
        self.core_range = tk.DoubleVar(value=14.0)
        self.pauli_range = tk.DoubleVar(value=30.0)
        self.beta_decay_rate = tk.DoubleVar(value=0.002)
        self.electron_core_strength = tk.DoubleVar(value=1.45)
        self.fusion_distance = tk.DoubleVar(value=38.0)
        self.fission_threshold = tk.DoubleVar(value=70.0)
        self.event_energy = tk.DoubleVar(value=2.4)
        self.damping = tk.DoubleVar(value=0.012)
        self.temperature = tk.DoubleVar(value=0.0)
        self.time_step = tk.DoubleVar(value=0.72)

        self.step_count = 0
        self.decay_count = 0
        self.fusion_count = 0
        self.fission_count = 0
        self.event_cooldown = 0
        self.pauli_contact_count = 0
        self.energy_value = tk.StringVar(value="에너지: 0.00")
        self.count_value = tk.StringVar(value="양성자: 0   중성자: 0")
        self.quantum_value = tk.StringVar(value="스핀 ↑ 0 / ↓ 0")
        self.selection_value = tk.StringVar(value="선택: 없음")
        self.selection_detail_value = tk.StringVar(value="입자를 클릭하면 세부 정보가 표시돼")
        self.mode_value = tk.StringVar(value="빈 공간 클릭: 입자 추가 | 드래그: 이동")
        self.energy_history: list[tuple[float, float, float]] = []

        self._build_ui()
        self._bind_events()
        self.load_scenario("helium")
        self._tick()

    def _build_ui(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Panel.TFrame", background=PANEL_BG)
        style.configure("Title.TLabel", background=PANEL_BG, foreground=TEXT, font=(FONT, 16, "bold"))
        style.configure("Body.TLabel", background=PANEL_BG, foreground=TEXT, font=(FONT, 9))
        style.configure("Muted.TLabel", background=PANEL_BG, foreground=MUTED, font=(FONT, 8))
        style.configure("TLabelframe", background=PANEL_BG)
        style.configure("TLabelframe.Label", background=PANEL_BG, foreground=TEXT, font=(FONT, 9, "bold"))
        style.configure("TButton", font=(FONT, 9))
        style.configure("TRadiobutton", background=PANEL_BG, foreground=TEXT, font=(FONT, 9))
        style.configure("TCheckbutton", background=PANEL_BG, foreground=TEXT, font=(FONT, 9))

        self.container = ttk.Frame(self.root)
        self.container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            self.container,
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            bg=BG,
            highlightthickness=0,
        )
        self.canvas.pack(side="left", fill="both", expand=True)

        panel_shell = ttk.Frame(self.container, width=PANEL_WIDTH, style="Panel.TFrame")
        panel_shell.pack(side="right", fill="y")
        panel_shell.pack_propagate(False)

        self.panel_canvas = tk.Canvas(panel_shell, bg=PANEL_BG, highlightthickness=0)
        panel_scrollbar = ttk.Scrollbar(panel_shell, orient="vertical", command=self.panel_canvas.yview)
        self.panel_canvas.configure(yscrollcommand=panel_scrollbar.set)
        panel_scrollbar.pack(side="right", fill="y")
        self.panel_canvas.pack(side="left", fill="both", expand=True)

        panel = ttk.Frame(self.panel_canvas, style="Panel.TFrame", padding=(14, 12))
        panel_window = self.panel_canvas.create_window((0, 0), window=panel, anchor="nw")

        def update_scroll_region(_event: tk.Event) -> None:
            self.panel_canvas.configure(scrollregion=self.panel_canvas.bbox("all"))

        def update_panel_width(event: tk.Event) -> None:
            self.panel_canvas.itemconfigure(panel_window, width=event.width)

        def scroll_panel(event: tk.Event) -> str:
            self.panel_canvas.yview_scroll(int(-event.delta / 120), "units")
            return "break"

        panel.bind("<Configure>", update_scroll_region)
        self.panel_canvas.bind("<Configure>", update_panel_width)
        self.panel_canvas.bind("<MouseWheel>", scroll_panel)
        panel.bind("<MouseWheel>", scroll_panel)

        ttk.Label(panel, text="핵자 샌드박스", style="Title.TLabel").pack(anchor="w")
        ttk.Label(panel, textvariable=self.mode_value, style="Muted.TLabel").pack(anchor="w", pady=(2, 12))

        row = ttk.Frame(panel, style="Panel.TFrame")
        row.pack(fill="x", pady=(0, 8))
        self.pause_button = ttk.Button(row, text="일시정지", command=self.toggle_running)
        self.pause_button.pack(side="left", expand=True, fill="x")
        ttk.Button(row, text="헬륨 초기화", command=lambda: self.load_scenario("helium")).pack(
            side="left", expand=True, fill="x", padx=(6, 0)
        )

        row2 = ttk.Frame(panel, style="Panel.TFrame")
        row2.pack(fill="x", pady=(0, 10))
        ttk.Button(row2, text="속도 0", command=self.freeze_velocities).pack(side="left", expand=True, fill="x")
        ttk.Button(row2, text="흔들기", command=self.random_kick).pack(side="left", expand=True, fill="x", padx=(6, 0))
        ttk.Button(row2, text="중앙", command=self.center_cluster).pack(side="left", expand=True, fill="x", padx=(6, 0))

        add_box = ttk.LabelFrame(panel, text="입자 추가", padding=8)
        add_box.pack(fill="x", pady=(0, 10))
        kind_row = ttk.Frame(add_box)
        kind_row.pack(fill="x")
        ttk.Radiobutton(kind_row, text="양성자", value=PROTON, variable=self.selected_kind).pack(side="left")
        ttk.Radiobutton(kind_row, text="중성자", value=NEUTRON, variable=self.selected_kind).pack(side="left", padx=(14, 0))
        ttk.Radiobutton(kind_row, text="전자", value=ELECTRON, variable=self.selected_kind).pack(side="left", padx=(14, 0))
        spin_row = ttk.Frame(add_box)
        spin_row.pack(fill="x", pady=(6, 0))
        ttk.Label(spin_row, text="스핀", style="Body.TLabel").pack(side="left")
        ttk.Radiobutton(spin_row, text="자동", value=SPIN_AUTO, variable=self.selected_spin).pack(side="left", padx=(8, 0))
        ttk.Radiobutton(spin_row, text="↑", value="up", variable=self.selected_spin).pack(side="left")
        ttk.Radiobutton(spin_row, text="↓", value="down", variable=self.selected_spin).pack(side="left")

        scenario = ttk.LabelFrame(panel, text="프리셋", padding=8)
        scenario.pack(fill="x", pady=(0, 10))
        for name, label in (
            ("hydrogen_atom", "수소 원자"),
            ("helium_atom", "헬륨 원자"),
            ("h2o_molecule", "물 분자 (H2O - VSEPR)"),
            ("ch4_molecule", "메탄 (CH4 - VSEPR)"),
            ("deuteron", "중수소"),
            ("helium", "헬륨-4"),
            ("oxygen", "산소-16"),
            ("carbon", "탄소-12"),
            ("iron", "철-56"),
            ("neutron_soup", "중성자 수프"),
            ("proton_ring", "양성자 링"),
            ("random", "무작위 혼합"),
            ("clear", "비우기"),
        ):
            ttk.Button(scenario, text=label, command=lambda n=name: self.load_scenario(n)).pack(fill="x", pady=2)

        files = ttk.LabelFrame(panel, text="상태 파일", padding=8)
        files.pack(fill="x", pady=(0, 10))
        ttk.Button(files, text="저장", command=self.save_state).pack(side="left", expand=True, fill="x")
        ttk.Button(files, text="불러오기", command=self.load_state).pack(side="left", expand=True, fill="x", padx=(6, 0))

        toggles = ttk.LabelFrame(panel, text="보기와 힘", padding=8)
        toggles.pack(fill="x", pady=(0, 10))
        for label, variable in (
            ("강한 핵력", self.strong_enabled),
            ("일반 전기력", self.electric_enabled),
            ("파울리 배타 압력", self.pauli_enabled),
            ("베타 붕괴/전환", self.beta_enabled),
            ("양방향 베타 안정화", self.beta_balance_enabled),
            ("핵융합 이벤트", self.fusion_enabled),
            ("핵분열 이벤트", self.fission_enabled),
            ("핵 결합선", self.bonds_enabled),
            ("파울리 압력선/스핀 표시", self.spin_labels_enabled),
            ("입자 궤적", self.trails_enabled),
            ("입자 라벨", self.labels_enabled),
            ("속도 화살표", self.velocity_enabled),
            ("붕괴 흔적", self.flashes_enabled),
        ):
            ttk.Checkbutton(toggles, text=label, variable=variable).pack(anchor="w")

        sliders = ttk.LabelFrame(panel, text="모델 조절", padding=8)
        sliders.pack(fill="x", pady=(0, 10))
        self._slider(sliders, "강한 인력", self.strong_strength, 0.0, 0.9)
        self._slider(sliders, "하드코어 반발", self.core_strength, 0.0, 1.3)
        self._slider(sliders, "전기 반발", self.electric_strength, 0.0, 220.0)
        self._slider(sliders, "파울리 세기", self.pauli_strength, 0.0, 4.0)
        self._slider(sliders, "전자 핵심 반발", self.electron_core_strength, 0.0, 4.0)
        self._slider(sliders, "강한 힘 범위", self.strong_range, 18.0, 90.0)
        self._slider(sliders, "코어 범위", self.core_range, 6.0, 28.0)
        self._slider(sliders, "파울리 범위", self.pauli_range, 12.0, 80.0)
        self._slider(sliders, "베타 붕괴율", self.beta_decay_rate, 0.0, 0.025, digits=4)
        self._slider(sliders, "융합 거리", self.fusion_distance, 20.0, 80.0)
        self._slider(sliders, "분열 임계값", self.fission_threshold, 12.0, 120.0)
        self._slider(sliders, "사건 에너지", self.event_energy, 0.2, 7.0)
        self._slider(sliders, "감쇠", self.damping, 0.0, 0.08, digits=3)
        self._slider(sliders, "온도 잡음", self.temperature, 0.0, 2.0)
        self._slider(sliders, "시간 간격", self.time_step, 0.12, 1.4)

        stats = ttk.LabelFrame(panel, text="상태", padding=8)
        stats.pack(fill="x")
        ttk.Label(stats, textvariable=self.count_value, style="Body.TLabel").pack(anchor="w")
        ttk.Label(stats, textvariable=self.quantum_value, style="Body.TLabel").pack(anchor="w")
        ttk.Label(stats, textvariable=self.energy_value, style="Body.TLabel").pack(anchor="w")
        ttk.Label(stats, textvariable=self.selection_value, style="Body.TLabel").pack(anchor="w", pady=(6, 0))
        ttk.Label(stats, textvariable=self.selection_detail_value, style="Muted.TLabel", wraplength=280).pack(anchor="w")
        self.energy_canvas = tk.Canvas(stats, height=58, bg="#ffffff", highlightthickness=1, highlightbackground="#d0cdc5")
        self.energy_canvas.pack(fill="x", pady=(6, 0))
        ttk.Label(stats, text="키: Space 정지, R 헬륨, C 비우기, P/N/E 입자", style="Muted.TLabel").pack(
            anchor="w", pady=(6, 0)
        )
        ttk.Label(stats, text="A 자동스핀, U/D 스핀, B 베타, F 융합, X 분열", style="Muted.TLabel").pack(anchor="w")
        ttk.Label(stats, text="우클릭: 가까운 입자 삭제", style="Muted.TLabel").pack(anchor="w")

    def _slider(
        self,
        parent: ttk.Frame,
        label: str,
        variable: tk.DoubleVar,
        low: float,
        high: float,
        digits: int = 2,
    ) -> None:
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=(0, 5))
        header = ttk.Frame(frame)
        header.pack(fill="x")
        value_text = tk.StringVar(value=f"{variable.get():.{digits}f}")

        def update_value(*_: object) -> None:
            value_text.set(f"{variable.get():.{digits}f}")

        variable.trace_add("write", update_value)
        ttk.Label(header, text=label, style="Body.TLabel").pack(side="left")
        ttk.Label(header, textvariable=value_text, style="Muted.TLabel").pack(side="right")
        ttk.Scale(frame, from_=low, to=high, variable=variable, orient="horizontal").pack(fill="x")

    def _bind_events(self) -> None:
        self.canvas.bind("<Button-1>", self.on_left_down)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_up)
        self.canvas.bind("<Button-3>", self.on_right_down)
        self.root.bind("<space>", lambda _event: self.toggle_running())
        self.root.bind("r", lambda _event: self.load_scenario("helium"))
        self.root.bind("R", lambda _event: self.load_scenario("helium"))
        self.root.bind("c", lambda _event: self.load_scenario("clear"))
        self.root.bind("C", lambda _event: self.load_scenario("clear"))
        self.root.bind("p", lambda _event: self.selected_kind.set(PROTON))
        self.root.bind("P", lambda _event: self.selected_kind.set(PROTON))
        self.root.bind("n", lambda _event: self.selected_kind.set(NEUTRON))
        self.root.bind("N", lambda _event: self.selected_kind.set(NEUTRON))
        self.root.bind("e", lambda _event: self.selected_kind.set(ELECTRON))
        self.root.bind("E", lambda _event: self.selected_kind.set(ELECTRON))
        self.root.bind("a", lambda _event: self.selected_spin.set(SPIN_AUTO))
        self.root.bind("A", lambda _event: self.selected_spin.set(SPIN_AUTO))
        self.root.bind("u", lambda _event: self.selected_spin.set("up"))
        self.root.bind("U", lambda _event: self.selected_spin.set("up"))
        self.root.bind("d", lambda _event: self.selected_spin.set("down"))
        self.root.bind("D", lambda _event: self.selected_spin.set("down"))
        self.root.bind("b", lambda _event: self._toggle_beta())
        self.root.bind("B", lambda _event: self._toggle_beta())
        self.root.bind("f", lambda _event: self._toggle_fusion())
        self.root.bind("F", lambda _event: self._toggle_fusion())
        self.root.bind("x", lambda _event: self._toggle_fission())
        self.root.bind("X", lambda _event: self._toggle_fission())

    def _toggle_beta(self) -> None:
        self.beta_enabled.set(not self.beta_enabled.get())
        self.mode_value.set("베타 붕괴 켜짐" if self.beta_enabled.get() else "베타 붕괴 꺼짐")

    def _toggle_fusion(self) -> None:
        self.fusion_enabled.set(not self.fusion_enabled.get())
        self.mode_value.set("핵융합 이벤트 켜짐" if self.fusion_enabled.get() else "핵융합 이벤트 꺼짐")

    def _toggle_fission(self) -> None:
        self.fission_enabled.set(not self.fission_enabled.get())
        self.mode_value.set("핵분열 이벤트 켜짐" if self.fission_enabled.get() else "핵분열 이벤트 꺼짐")

    def toggle_running(self) -> None:
        self.running = not self.running
        self.pause_button.configure(text="일시정지" if self.running else "재개")
        self.mode_value.set("실행 중" if self.running else "일시정지")

    def freeze_velocities(self) -> None:
        for particle in self.particles:
            particle.vx = 0.0
            particle.vy = 0.0
        self.mode_value.set("모든 속도를 0으로 만들었어")

    def random_kick(self) -> None:
        for particle in self.particles:
            particle.vx += random.uniform(-2.2, 2.2)
            particle.vy += random.uniform(-2.2, 2.2)
        self.mode_value.set("무작위 운동량을 줬어")

    def center_cluster(self) -> None:
        if not self.particles:
            return
        avg_x = sum(p.x for p in self.particles) / len(self.particles)
        avg_y = sum(p.y for p in self.particles) / len(self.particles)
        dx = self.canvas_width / 2.0 - avg_x
        dy = self.canvas_height / 2.0 - avg_y
        for particle in self.particles:
            particle.x += dx
            particle.y += dy
            particle.trail.clear()
        self.mode_value.set("핵자 무리를 중앙으로 옮겼어")

    def save_state(self) -> None:
        path = filedialog.asksaveasfilename(
            title="핵자 상태 저장",
            defaultextension=".json",
            filetypes=(("JSON 파일", "*.json"), ("모든 파일", "*.*")),
        )
        if not path:
            return
        data = {
            "version": 2,
            "particles": [
                {
                    "kind": p.kind,
                    "x": p.x,
                    "y": p.y,
                    "vx": p.vx,
                    "vy": p.vy,
                    "mass": p.mass,
                    "spin": p.spin,
                }
                for p in self.particles
            ],
            "knobs": self._knob_values(),
            "toggles": self._toggle_values(),
        }
        try:
            with open(path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
        except OSError as exc:
            messagebox.showerror("저장 실패", str(exc))
            return
        self.mode_value.set("상태를 저장했어")

    def load_state(self) -> None:
        path = filedialog.askopenfilename(
            title="핵자 상태 불러오기",
            filetypes=(("JSON 파일", "*.json"), ("모든 파일", "*.*")),
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError) as exc:
            messagebox.showerror("불러오기 실패", str(exc))
            return

        particles = data.get("particles", [])
        if not isinstance(particles, list):
            messagebox.showerror("불러오기 실패", "상태 파일에 입자 목록이 없어.")
            return

        self.particles.clear()
        for item in particles[:MAX_PARTICLES]:
            if not isinstance(item, dict):
                continue
            kind = item.get("kind")
            if kind not in (PROTON, NEUTRON, ELECTRON):
                continue
            self.particles.append(
                Particle(
                    kind=kind,
                    x=float(item.get("x", self.canvas_width / 2)),
                    y=float(item.get("y", self.canvas_height / 2)),
                    vx=float(item.get("vx", 0.0)),
                    vy=float(item.get("vy", 0.0)),
                    mass=float(item.get("mass", self._default_mass(kind))),
                    spin=self._parse_spin(item.get("spin", SPIN_UP)),
                )
            )

        self._apply_knob_values(data.get("knobs", {}))
        self._apply_toggle_values(data.get("toggles", {}))
        self.energy_history.clear()
        self.flashes.clear()
        self.mode_value.set("상태를 불러왔어")

    def _knob_values(self) -> dict[str, float]:
        return {
            "strong_strength": self.strong_strength.get(),
            "core_strength": self.core_strength.get(),
            "electric_strength": self.electric_strength.get(),
            "pauli_strength": self.pauli_strength.get(),
            "strong_range": self.strong_range.get(),
            "core_range": self.core_range.get(),
            "pauli_range": self.pauli_range.get(),
            "beta_decay_rate": self.beta_decay_rate.get(),
            "electron_core_strength": self.electron_core_strength.get(),
            "fusion_distance": self.fusion_distance.get(),
            "fission_threshold": self.fission_threshold.get(),
            "event_energy": self.event_energy.get(),
            "damping": self.damping.get(),
            "temperature": self.temperature.get(),
            "time_step": self.time_step.get(),
        }

    def _toggle_values(self) -> dict[str, bool]:
        return {
            "strong_enabled": self.strong_enabled.get(),
            "electric_enabled": self.electric_enabled.get(),
            "pauli_enabled": self.pauli_enabled.get(),
            "beta_enabled": self.beta_enabled.get(),
            "beta_balance_enabled": self.beta_balance_enabled.get(),
            "fusion_enabled": self.fusion_enabled.get(),
            "fission_enabled": self.fission_enabled.get(),
            "trails_enabled": self.trails_enabled.get(),
            "labels_enabled": self.labels_enabled.get(),
            "spin_labels_enabled": self.spin_labels_enabled.get(),
            "bonds_enabled": self.bonds_enabled.get(),
            "velocity_enabled": self.velocity_enabled.get(),
            "flashes_enabled": self.flashes_enabled.get(),
        }

    def _apply_knob_values(self, values: object) -> None:
        if not isinstance(values, dict):
            return
        knobs = {
            "strong_strength": self.strong_strength,
            "core_strength": self.core_strength,
            "electric_strength": self.electric_strength,
            "pauli_strength": self.pauli_strength,
            "strong_range": self.strong_range,
            "core_range": self.core_range,
            "pauli_range": self.pauli_range,
            "beta_decay_rate": self.beta_decay_rate,
            "electron_core_strength": self.electron_core_strength,
            "fusion_distance": self.fusion_distance,
            "fission_threshold": self.fission_threshold,
            "event_energy": self.event_energy,
            "damping": self.damping,
            "temperature": self.temperature,
            "time_step": self.time_step,
        }
        for key, variable in knobs.items():
            if key in values:
                variable.set(float(values[key]))

    def _apply_toggle_values(self, values: object) -> None:
        if not isinstance(values, dict):
            return
        toggles = {
            "strong_enabled": self.strong_enabled,
            "electric_enabled": self.electric_enabled,
            "pauli_enabled": self.pauli_enabled,
            "beta_enabled": self.beta_enabled,
            "beta_balance_enabled": self.beta_balance_enabled,
            "fusion_enabled": self.fusion_enabled,
            "fission_enabled": self.fission_enabled,
            "trails_enabled": self.trails_enabled,
            "labels_enabled": self.labels_enabled,
            "spin_labels_enabled": self.spin_labels_enabled,
            "bonds_enabled": self.bonds_enabled,
            "velocity_enabled": self.velocity_enabled,
            "flashes_enabled": self.flashes_enabled,
        }
        for key, variable in toggles.items():
            if key in values:
                variable.set(bool(values[key]))

    def load_scenario(self, name: str) -> None:
        self.particles.clear()
        self.flashes.clear()
        self.energy_history.clear()
        self.selected_index = None
        self.step_count = 0
        center_x = self.canvas_width / 2
        center_y = self.canvas_height / 2

        if name == "clear":
            self.running = False
            self.pause_button.configure(text="재개")
            self.mode_value.set("빈 샌드박스")
            return

        if name == "hydrogen_atom":
            self.add_particle(PROTON, center_x, center_y, 0.0, 0.0, spin=SPIN_UP)
            self._spawn_orbiting_electrons(center_x, center_y, count=1, radius=80)
        elif name == "helium_atom":
            self.add_particle(PROTON, center_x - 18, center_y - 14, 0.05, -0.05, spin=SPIN_UP)
            self.add_particle(PROTON, center_x + 18, center_y + 14, -0.05, 0.05, spin=SPIN_DOWN)
            self.add_particle(NEUTRON, center_x + 14, center_y - 18, -0.05, -0.05, spin=SPIN_UP)
            self.add_particle(NEUTRON, center_x - 14, center_y + 18, 0.05, 0.05, spin=SPIN_DOWN)
            self._spawn_orbiting_electrons(center_x, center_y, count=2, radius=92)
        elif name == "deuteron":
            self.add_particle(PROTON, center_x - 18, center_y, 0.0, -0.2, spin=SPIN_UP)
            self.add_particle(NEUTRON, center_x + 18, center_y, 0.0, 0.2, spin=SPIN_UP)
        elif name == "helium":
            self.add_particle(PROTON, center_x - 18, center_y - 14, 0.16, -0.12, spin=SPIN_UP)
            self.add_particle(PROTON, center_x + 18, center_y + 14, -0.16, 0.12, spin=SPIN_DOWN)
            self.add_particle(NEUTRON, center_x + 14, center_y - 18, -0.08, -0.16, spin=SPIN_UP)
            self.add_particle(NEUTRON, center_x - 14, center_y + 18, 0.08, 0.16, spin=SPIN_DOWN)
        elif name == "oxygen":
            self._spawn_cluster(center_x, center_y, protons=8, neutrons=8, radius=72)
        elif name == "carbon":
            self._spawn_cluster(center_x, center_y, protons=6, neutrons=6, radius=56)
        elif name == "iron":
            self._spawn_cluster(center_x, center_y, protons=26, neutrons=30, radius=145)
        elif name == "neutron_soup":
            self._spawn_cluster(center_x, center_y, protons=0, neutrons=22, radius=140)
        elif name == "proton_ring":
            self._spawn_ring(center_x, center_y, kind=PROTON, count=20, radius=145)
        elif name == "random":
            self._spawn_cluster(center_x, center_y, protons=12, neutrons=16, radius=190, randomize=True)

        self.running = True
        self.pause_button.configure(text="일시정지")
        self.mode_value.set(f"{self._scenario_name(name)} 불러옴")

    def _scenario_name(self, name: str) -> str:
        return {
            "hydrogen_atom": "수소 원자",
            "helium_atom": "헬륨 원자",
            "deuteron": "중수소",
            "helium": "헬륨-4",
            "oxygen": "산소-16",
            "carbon": "탄소-12",
            "iron": "철-56",
            "neutron_soup": "중성자 수프",
            "proton_ring": "양성자 링",
            "random": "무작위 혼합",
            "clear": "비우기",
        }.get(name, name)

    def _spawn_orbiting_electrons(self, cx: float, cy: float, count: int, radius: float) -> None:
        for i in range(count):
            angle = i / max(1, count) * math.tau
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius
            tangent = angle + math.pi / 2.0
            speed = 1.2 / math.sqrt(max(0.5, radius / 80.0))
            spin = SPIN_UP if i % 2 == 0 else SPIN_DOWN
            self.add_particle(ELECTRON, x, y, math.cos(tangent) * speed, math.sin(tangent) * speed, spin=spin)

    def _spawn_cluster(
        self,
        cx: float,
        cy: float,
        protons: int,
        neutrons: int,
        radius: float,
        randomize: bool = False,
    ) -> None:
        kinds = [PROTON] * protons + [NEUTRON] * neutrons
        random.shuffle(kinds)
        spin_counts = {PROTON: 0, NEUTRON: 0}
        for i, kind in enumerate(kinds):
            if randomize:
                angle = random.random() * math.tau
                distance = radius * math.sqrt(random.random())
            else:
                angle = i * math.pi * (3.0 - math.sqrt(5.0))
                distance = radius * math.sqrt((i + 0.5) / max(1, len(kinds)))
            x = cx + math.cos(angle) * distance
            y = cy + math.sin(angle) * distance
            tangent = angle + math.pi / 2.0
            speed = 0.25 + random.random() * 0.35
            spin = SPIN_UP if spin_counts[kind] % 2 == 0 else SPIN_DOWN
            spin_counts[kind] += 1
            self.add_particle(kind, x, y, math.cos(tangent) * speed, math.sin(tangent) * speed, spin=spin)

    def _spawn_ring(self, cx: float, cy: float, kind: str, count: int, radius: float) -> None:
        for i in range(count):
            angle = i / count * math.tau
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius
            tangent = angle + math.pi / 2
            spin = SPIN_UP if i % 2 == 0 else SPIN_DOWN
            self.add_particle(kind, x, y, math.cos(tangent) * 0.7, math.sin(tangent) * 0.7, spin=spin)

    @property
    def canvas_width(self) -> float:
        actual = self.canvas.winfo_width()
        return float(actual if actual > 2 else CANVAS_WIDTH)

    @property
    def canvas_height(self) -> float:
        actual = self.canvas.winfo_height()
        return float(actual if actual > 2 else CANVAS_HEIGHT)

    def _default_mass(self, kind: str) -> float:
        if kind == ELECTRON:
            return 0.08
        if kind == NEUTRON:
            return 1.001
        return 1.0

    def _is_nucleon(self, particle: Particle) -> bool:
        return particle.kind in (PROTON, NEUTRON)

    def add_particle(
        self,
        kind: str,
        x: float,
        y: float,
        vx: float | None = None,
        vy: float | None = None,
        spin: int | None = None,
    ) -> None:
        if len(self.particles) >= MAX_PARTICLES:
            self.mode_value.set(f"입자 수 한계: {MAX_PARTICLES}")
            return
        if vx is None:
            vx = random.uniform(-0.4, 0.4)
        if vy is None:
            vy = random.uniform(-0.4, 0.4)
        if spin is None:
            spin = self._choose_spin(kind, x, y)
        mass = self._default_mass(kind)
        self.particles.append(Particle(kind=kind, x=x, y=y, vx=vx, vy=vy, mass=mass, spin=spin))

    def _choose_spin(self, kind: str, x: float, y: float) -> int:
        selected = self.selected_spin.get()
        if selected == "up":
            return SPIN_UP
        if selected == "down":
            return SPIN_DOWN
        return self._least_crowded_spin(kind, x, y)

    def _least_crowded_spin(self, kind: str, x: float, y: float) -> int:
        scores = {SPIN_UP: 0.0, SPIN_DOWN: 0.0}
        scale = max(1.0, self.pauli_range.get())
        for particle in self.particles:
            if particle.kind != kind:
                continue
            dx = particle.x - x
            dy = particle.y - y
            distance = math.hypot(dx, dy)
            scores[particle.spin] += math.exp(-((distance / scale) ** 2))
        if abs(scores[SPIN_UP] - scores[SPIN_DOWN]) < 0.001:
            return random.choice((SPIN_UP, SPIN_DOWN))
        return SPIN_UP if scores[SPIN_UP] < scores[SPIN_DOWN] else SPIN_DOWN

    def _parse_spin(self, value: object) -> int:
        if value in (SPIN_DOWN, "down", "DOWN", "↓", "-1"):
            return SPIN_DOWN
        return SPIN_UP

    def on_left_down(self, event: tk.Event) -> None:
        index = self.nearest_particle(event.x, event.y, radius=18.0)
        if index is None:
            kind = self.selected_kind.get()
            self.add_particle(kind, event.x, event.y)
            self.selected_index = len(self.particles) - 1
            self.mode_value.set(f"{KIND_KO[kind]} 추가")
            return
        self.selected_index = index
        self.dragged_index = index
        self.drag_previous = (event.x, event.y)
        self.particles[index].vx = 0.0
        self.particles[index].vy = 0.0
        particle = self.particles[index]
        self.mode_value.set(f"{particle.korean_name}{particle.spin_symbol} 드래그 중")

    def on_drag(self, event: tk.Event) -> None:
        if self.dragged_index is None:
            return
        particle = self.particles[self.dragged_index]
        if self.drag_previous is not None:
            px, py = self.drag_previous
            particle.vx = (event.x - px) * 0.25
            particle.vy = (event.y - py) * 0.25
        radius = particle.radius
        particle.x = min(max(radius, float(event.x)), self.canvas_width - radius)
        particle.y = min(max(radius, float(event.y)), self.canvas_height - radius)
        self.drag_previous = (event.x, event.y)

    def on_left_up(self, _event: tk.Event) -> None:
        self.dragged_index = None
        self.drag_previous = None
        self.mode_value.set("실행 중" if self.running else "일시정지")

    def on_right_down(self, event: tk.Event) -> None:
        index = self.nearest_particle(event.x, event.y, radius=24.0)
        if index is not None:
            removed = self.particles.pop(index)
            if self.selected_index == index:
                self.selected_index = None
            elif self.selected_index is not None and self.selected_index > index:
                self.selected_index -= 1
            self.mode_value.set(f"{removed.korean_name} 삭제")

    def nearest_particle(self, x: float, y: float, radius: float) -> int | None:
        best_index = None
        best_distance = radius * radius
        for i, particle in enumerate(self.particles):
            dx = particle.x - x
            dy = particle.y - y
            distance_sq = dx * dx + dy * dy
            if distance_sq <= best_distance:
                best_index = i
                best_distance = distance_sq
        return best_index

    def _tick(self) -> None:
        if self.running:
            self.step()
        self.draw()
        self.update_stats()
        self.root.after(16, self._tick)

    def step(self) -> None:
        dt = self.time_step.get()
        substeps = 3
        sub_dt = dt / substeps

        for _ in range(substeps):
            forces = self.compute_forces()
            for i, particle in enumerate(self.particles):
                if i == self.dragged_index:
                    continue
                fx, fy = forces[i]
                particle.vx += (fx / particle.mass) * sub_dt
                particle.vy += (fy / particle.mass) * sub_dt

                temp = self.temperature.get()
                if temp > 0.0:
                    particle.vx += random.gauss(0.0, temp * 0.015)
                    particle.vy += random.gauss(0.0, temp * 0.015)

                damping = max(0.0, min(0.25, self.damping.get()))
                particle.vx *= 1.0 - damping
                particle.vy *= 1.0 - damping

                speed = math.hypot(particle.vx, particle.vy)
                if speed > MAX_SPEED:
                    scale = MAX_SPEED / speed
                    particle.vx *= scale
                    particle.vy *= scale

                particle.x += particle.vx * sub_dt
                particle.y += particle.vy * sub_dt
                self._contain_particle(particle)

        if self.event_cooldown > 0:
            self.event_cooldown -= 1
        self._apply_nuclear_events(dt)
        self._apply_beta_decay(dt)
        self._update_flashes(dt)
        self.step_count += 1
        self._record_trails()

    def _apply_nuclear_events(self, dt: float) -> None:
        if self.event_cooldown > 0:
            return
        components = self._nucleon_components()
        if self.fusion_enabled.get() and len(components) >= 2 and self._try_fusion(components):
            self.event_cooldown = 34
            return
        if self.fission_enabled.get() and components:
            if self._try_fission(components, dt):
                self.event_cooldown = 46

    def _nucleon_components(self) -> list[list[int]]:
        indices = [i for i, particle in enumerate(self.particles) if self._is_nucleon(particle)]
        if not indices:
            return []
        parent = {i: i for i in indices}

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: int, b: int) -> None:
            root_a = find(a)
            root_b = find(b)
            if root_a != root_b:
                parent[root_b] = root_a

        link_distance = self.strong_range.get() * 0.82
        for pos, i in enumerate(indices):
            a = self.particles[i]
            for j in indices[pos + 1 :]:
                b = self.particles[j]
                if math.hypot(b.x - a.x, b.y - a.y) < link_distance:
                    union(i, j)

        groups: dict[int, list[int]] = {}
        for i in indices:
            groups.setdefault(find(i), []).append(i)
        return list(groups.values())

    def _component_center(self, component: list[int]) -> tuple[float, float, float, float, float]:
        total_mass = sum(self.particles[i].mass for i in component)
        if total_mass <= 0:
            total_mass = 1.0
        cx = sum(self.particles[i].x * self.particles[i].mass for i in component) / total_mass
        cy = sum(self.particles[i].y * self.particles[i].mass for i in component) / total_mass
        vx = sum(self.particles[i].vx * self.particles[i].mass for i in component) / total_mass
        vy = sum(self.particles[i].vy * self.particles[i].mass for i in component) / total_mass
        return cx, cy, vx, vy, total_mass

    def _try_fusion(self, components: list[list[int]]) -> bool:
        distance_limit = self.fusion_distance.get()
        best: tuple[float, list[int], list[int]] | None = None
        for i, first in enumerate(components):
            if not first:
                continue
            c1x, c1y, v1x, v1y, _m1 = self._component_center(first)
            for second in components[i + 1 :]:
                if not second:
                    continue
                c2x, c2y, v2x, v2y, _m2 = self._component_center(second)
                center_distance = math.hypot(c2x - c1x, c2y - c1y)
                relative_speed = math.hypot(v2x - v1x, v2y - v1y)
                pair_distance = self._minimum_component_distance(first, second)
                if pair_distance < distance_limit and relative_speed < 6.0:
                    score = pair_distance + center_distance * 0.15 + relative_speed * 2.0
                    if best is None or score < best[0]:
                        best = (score, first, second)
        if best is None:
            return False
        self._fuse_components(best[1], best[2])
        return True

    def _minimum_component_distance(self, first: list[int], second: list[int]) -> float:
        result = float("inf")
        for i in first:
            a = self.particles[i]
            for j in second:
                b = self.particles[j]
                result = min(result, math.hypot(b.x - a.x, b.y - a.y))
        return result

    def _fuse_components(self, first: list[int], second: list[int]) -> None:
        merged = first + second
        cx, cy, vx, vy, _mass = self._component_center(merged)
        energy = self.event_energy.get()
        for i in merged:
            particle = self.particles[i]
            dx = cx - particle.x
            dy = cy - particle.y
            distance = math.hypot(dx, dy) or 1.0
            particle.vx = vx + dx / distance * min(1.6, distance * 0.015) + random.uniform(-0.25, 0.25)
            particle.vy = vy + dy / distance * min(1.6, distance * 0.015) + random.uniform(-0.25, 0.25)
            particle.trail.clear()
        for _ in range(5):
            self._add_flash(cx, cy, random.random() * math.tau, "융합", "#f2c14e")
        self.fusion_count += 1
        self.mode_value.set("핵융합 이벤트 발생")
        self._radiate_event_energy(cx, cy, energy * 0.35, label="γ")

    def _try_fission(self, components: list[list[int]], dt: float) -> bool:
        threshold = max(4.0, self.fission_threshold.get())
        for component in sorted(components, key=len, reverse=True):
            if len(component) < threshold:
                continue
            protons = sum(1 for i in component if self.particles[i].kind == PROTON)
            neutrons = len(component) - protons
            proton_excess = max(0, protons - neutrons * 0.75)
            size_pressure = len(component) / threshold - 1.0
            coulomb_pressure = proton_excess / max(1.0, len(component)) * 2.5
            chance = dt * 0.0035 * max(0.0, size_pressure + coulomb_pressure)
            if random.random() < chance:
                self._split_component(component)
                return True
        return False

    def _split_component(self, component: list[int]) -> None:
        if len(component) < 4:
            return
        cx, cy, vx, vy, _mass = self._component_center(component)
        axis = random.random() * math.tau
        ux = math.cos(axis)
        uy = math.sin(axis)
        sorted_component = sorted(component, key=lambda i: (self.particles[i].x - cx) * ux + (self.particles[i].y - cy) * uy)
        midpoint = len(sorted_component) // 2
        left = sorted_component[:midpoint]
        right = sorted_component[midpoint:]
        energy = self.event_energy.get()
        for group, sign in ((left, -1.0), (right, 1.0)):
            for i in group:
                particle = self.particles[i]
                particle.vx = vx + ux * sign * energy + random.uniform(-0.7, 0.7)
                particle.vy = vy + uy * sign * energy + random.uniform(-0.7, 0.7)
                particle.x += ux * sign * 5.0
                particle.y += uy * sign * 5.0
                particle.trail.clear()
        for _ in range(7):
            self._add_flash(cx, cy, random.random() * math.tau, "분열", "#ff6b6b")
        self.fission_count += 1
        self.mode_value.set("핵분열 이벤트 발생")
        self._radiate_event_energy(cx, cy, energy * 0.55, label="γ")

    def _radiate_event_energy(self, x: float, y: float, energy: float, label: str) -> None:
        for _ in range(max(1, int(energy * 2))):
            self._add_flash(x, y, random.random() * math.tau, label, "#ffffff")

    def compute_forces(self) -> list[tuple[float, float]]:
        forces = [[0.0, 0.0] for _ in self.particles]
        count = len(self.particles)
        pauli_contacts = 0
        for i in range(count):
            a = self.particles[i]
            for j in range(i + 1, count):
                b = self.particles[j]
                dx = b.x - a.x
                dy = b.y - a.y
                distance = math.hypot(dx, dy)
                if distance < 0.001:
                    angle = random.random() * math.tau
                    dx = math.cos(angle)
                    dy = math.sin(angle)
                    distance = 1.0
                unit_x = dx / distance
                unit_y = dy / distance
                r = max(distance, MIN_DISTANCE)

                magnitude = 0.0
                if self.strong_enabled.get() and self._is_nucleon(a) and self._is_nucleon(b):
                    magnitude += self._strong_magnitude(r)
                if self.electric_enabled.get() and a.charge and b.charge:
                    magnitude += self._electric_magnitude(a.charge, b.charge, r)
                    if self._is_electron_nucleus_pair(a, b):
                        magnitude -= self._electron_core_magnitude(r)
                if self.pauli_enabled.get() and self._same_quantum_bucket(a, b):
                    magnitude -= self._pauli_magnitude(r)
                    if r < self.pauli_range.get():
                        pauli_contacts += 1

                magnitude = max(-MAX_FORCE, min(MAX_FORCE, magnitude))
                fx = unit_x * magnitude
                fy = unit_y * magnitude
                forces[i][0] += fx
                forces[i][1] += fy
                forces[j][0] -= fx
                forces[j][1] -= fy
        self.pauli_contact_count = pauli_contacts
        return [(fx, fy) for fx, fy in forces]

    def _same_quantum_bucket(self, a: Particle, b: Particle) -> bool:
        return a.kind == b.kind and a.spin == b.spin

    def _is_electron_nucleus_pair(self, a: Particle, b: Particle) -> bool:
        return (a.kind == ELECTRON and b.kind == PROTON) or (a.kind == PROTON and b.kind == ELECTRON)

    def _strong_magnitude(self, r: float) -> float:
        attract_range = max(4.0, self.strong_range.get())
        core_range = max(2.0, self.core_range.get())
        cutoff = attract_range * 3.4
        if r > cutoff:
            return 0.0

        attraction = self.strong_strength.get() * math.exp(-r / attract_range)
        core = self.core_strength.get() * math.exp(-r / core_range)
        taper = (1.0 - r / cutoff) ** 2
        return (attraction - core) * taper

    def _electric_magnitude(self, charge_a: float, charge_b: float, r: float) -> float:
        return -self.electric_strength.get() * charge_a * charge_b / (r * r + 55.0)

    def _electron_core_magnitude(self, r: float) -> float:
        return self.electron_core_strength.get() * math.exp(-((r / 16.0) ** 2))

    def _pauli_magnitude(self, r: float) -> float:
        scale = max(1.0, self.pauli_range.get())
        return self.pauli_strength.get() * math.exp(-((r / scale) ** 2))

    def _strong_potential(self, r: float) -> float:
        attract_range = max(4.0, self.strong_range.get())
        core_range = max(2.0, self.core_range.get())
        cutoff = attract_range * 3.4
        if r > cutoff:
            return 0.0
        taper = (1.0 - r / cutoff) ** 2
        attraction = -self.strong_strength.get() * attract_range * math.exp(-r / attract_range)
        core = self.core_strength.get() * core_range * math.exp(-r / core_range)
        return (attraction + core) * taper

    def _electric_potential(self, charge_a: float, charge_b: float, r: float) -> float:
        return self.electric_strength.get() * charge_a * charge_b / math.sqrt(r * r + 55.0)

    def _pauli_potential(self, r: float) -> float:
        scale = max(1.0, self.pauli_range.get())
        return self.pauli_strength.get() * scale * math.exp(-((r / scale) ** 2))

    def _apply_beta_decay(self, dt: float) -> None:
        if not self.beta_enabled.get():
            return
        rate = self.beta_decay_rate.get()
        if rate <= 0.0 or not self.particles:
            return

        protons = sum(1 for p in self.particles if p.kind == PROTON)
        neutrons = sum(1 for p in self.particles if p.kind == NEUTRON)
        changed = 0
        changed += self._try_electron_capture(rate, dt, protons, neutrons)
        protons = sum(1 for p in self.particles if p.kind == PROTON)
        neutrons = sum(1 for p in self.particles if p.kind == NEUTRON)
        for particle in list(self.particles):
            if particle.kind == NEUTRON:
                isolation = 1.8 if self._neighbor_count(particle) == 0 else 0.2
                excess = max(0, neutrons - protons - 2) * 0.22
                chance = rate * (0.7 + isolation + excess) * dt
                if random.random() < chance:
                    self._convert_particle(particle, PROTON, "beta_minus")
                    protons += 1
                    neutrons -= 1
                    changed += 1
            elif particle.kind == PROTON and self.beta_balance_enabled.get() and protons > neutrons + 2:
                excess = protons - neutrons - 2
                chance = rate * 0.25 * excess * dt
                if random.random() < chance:
                    self._convert_particle(particle, NEUTRON, "beta_plus")
                    protons -= 1
                    neutrons += 1
                    changed += 1

        if changed:
            self.decay_count += changed
            self.mode_value.set(f"베타 전환 {changed}회 발생")

    def _try_electron_capture(self, rate: float, dt: float, protons: int, neutrons: int) -> int:
        if not self.beta_balance_enabled.get() or protons <= neutrons + 1:
            return 0
        electrons = [p for p in self.particles if p.kind == ELECTRON]
        if not electrons:
            return 0
        for proton in [p for p in self.particles if p.kind == PROTON]:
            nearest = min(electrons, key=lambda e: math.hypot(e.x - proton.x, e.y - proton.y), default=None)
            if nearest is None:
                continue
            distance = math.hypot(nearest.x - proton.x, nearest.y - proton.y)
            if distance > 18.0:
                continue
            chance = rate * (protons - neutrons) * 0.7 * dt
            if random.random() < chance:
                removed_index = self.particles.index(nearest)
                self.particles.pop(removed_index)
                if self.selected_index == removed_index:
                    self.selected_index = None
                elif self.selected_index is not None and self.selected_index > removed_index:
                    self.selected_index -= 1
                self._convert_particle(proton, NEUTRON, "electron_capture")
                self._add_flash(proton.x, proton.y, random.random() * math.tau, "ν", "#9bf6ff")
                return 1
        return 0

    def _neighbor_count(self, target: Particle) -> int:
        count = 0
        limit = self.strong_range.get() * 1.45
        for particle in self.particles:
            if particle is target:
                continue
            if not self._is_nucleon(particle):
                continue
            if math.hypot(particle.x - target.x, particle.y - target.y) < limit:
                count += 1
        return count

    def _convert_particle(self, particle: Particle, new_kind: str, mode: str) -> None:
        old_x, old_y = particle.x, particle.y
        old_kind = particle.kind
        angle = random.random() * math.tau
        recoil = random.uniform(1.2, 2.5)
        particle.vx += math.cos(angle + math.pi) * recoil
        particle.vy += math.sin(angle + math.pi) * recoil
        particle.kind = new_kind
        particle.mass = self._default_mass(new_kind)
        particle.spin = self._least_crowded_spin(new_kind, particle.x, particle.y)
        particle.trail.clear()

        if mode == "beta_minus":
            self._add_flash(old_x, old_y, angle, "e-", "#ffd166")
            self._add_flash(old_x, old_y, angle + 1.9, "ν̅", "#9bf6ff")
        elif mode == "beta_plus":
            self._add_flash(old_x, old_y, angle, "e+", "#ffafcc")
            self._add_flash(old_x, old_y, angle + 1.9, "ν", "#9bf6ff")
        elif mode == "electron_capture":
            self._add_flash(old_x, old_y, angle, "포획", "#f2c14e")

        self.mode_value.set(f"{KIND_KO[old_kind]} → {KIND_KO[new_kind]} 베타 전환")

    def _add_flash(self, x: float, y: float, angle: float, label: str, color: str) -> None:
        speed = random.uniform(2.8, 4.5)
        self.flashes.append(DecayFlash(x=x, y=y, vx=math.cos(angle) * speed, vy=math.sin(angle) * speed, label=label, color=color))
        if len(self.flashes) > 80:
            del self.flashes[: len(self.flashes) - 80]

    def _update_flashes(self, dt: float) -> None:
        alive: list[DecayFlash] = []
        for flash in self.flashes:
            flash.x += flash.vx * dt
            flash.y += flash.vy * dt
            flash.life -= 1
            if flash.life > 0:
                alive.append(flash)
        self.flashes = alive

    def _contain_particle(self, particle: Particle) -> None:
        radius = particle.radius
        width = self.canvas_width
        height = self.canvas_height
        bounce = 0.72

        if particle.x < radius:
            particle.x = radius
            particle.vx = abs(particle.vx) * bounce
        elif particle.x > width - radius:
            particle.x = width - radius
            particle.vx = -abs(particle.vx) * bounce

        if particle.y < radius:
            particle.y = radius
            particle.vy = abs(particle.vy) * bounce
        elif particle.y > height - radius:
            particle.y = height - radius
            particle.vy = -abs(particle.vy) * bounce

    def _record_trails(self) -> None:
        if not self.trails_enabled.get():
            for particle in self.particles:
                particle.trail.clear()
            return
        for particle in self.particles:
            particle.trail.append((particle.x, particle.y))
            if len(particle.trail) > 42:
                del particle.trail[0]

    def draw(self) -> None:
        self.canvas.delete("all")
        width = self.canvas_width
        height = self.canvas_height
        self._draw_grid(width, height)
        if self.trails_enabled.get():
            self._draw_trails()
        if self.bonds_enabled.get():
            self._draw_bonds()
        if self.pauli_enabled.get() and self.spin_labels_enabled.get():
            self._draw_pauli_pressure()
        if self.velocity_enabled.get():
            self._draw_velocities()
        if self.flashes_enabled.get():
            self._draw_flashes()
        self._draw_particles()
        self._draw_energy_history()

    def _draw_grid(self, width: float, height: float) -> None:
        spacing = 48
        for x in range(0, int(width), spacing):
            self.canvas.create_line(x, 0, x, height, fill=GRID)
        for y in range(0, int(height), spacing):
            self.canvas.create_line(0, y, width, y, fill=GRID)
        self.canvas.create_text(
            12,
            12,
            text="토이 모델: 강한 핵력 + 일반 전기력 + 파울리 배타 압력 + 베타/융합/분열 이벤트",
            fill="#d5dde5",
            anchor="nw",
            font=(FONT, 9),
        )

    def _draw_trails(self) -> None:
        for particle in self.particles:
            if len(particle.trail) < 2:
                continue
            if particle.kind == PROTON:
                color = TRAIL_PROTON
            elif particle.kind == ELECTRON:
                color = TRAIL_ELECTRON
            else:
                color = TRAIL_NEUTRON
            for i in range(1, len(particle.trail)):
                x1, y1 = particle.trail[i - 1]
                x2, y2 = particle.trail[i]
                width = 1 + i / 20.0
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)

    def _draw_bonds(self) -> None:
        if not self.strong_enabled.get():
            return
        max_bond = self.strong_range.get() * 1.35
        for i, a in enumerate(self.particles):
            if not self._is_nucleon(a):
                continue
            for b in self.particles[i + 1 :]:
                if not self._is_nucleon(b):
                    continue
                dx = b.x - a.x
                dy = b.y - a.y
                distance = math.hypot(dx, dy)
                if 14.0 < distance < max_bond and self._strong_magnitude(distance) > 0.015:
                    intensity = max(0.18, 1.0 - distance / max_bond)
                    width = 1 + intensity * 3
                    self.canvas.create_line(a.x, a.y, b.x, b.y, fill=BOND, width=width)

    def _draw_pauli_pressure(self) -> None:
        limit = self.pauli_range.get()
        if limit <= 1:
            return
        for i, a in enumerate(self.particles):
            for b in self.particles[i + 1 :]:
                if not self._same_quantum_bucket(a, b):
                    continue
                distance = math.hypot(b.x - a.x, b.y - a.y)
                if distance < limit:
                    width = max(1.0, 3.0 * (1.0 - distance / limit))
                    self.canvas.create_line(a.x, a.y, b.x, b.y, fill=PAULI_LINE, width=width, dash=(3, 4))

    def _draw_velocities(self) -> None:
        for particle in self.particles:
            speed = math.hypot(particle.vx, particle.vy)
            if speed < 0.08:
                continue
            x2 = particle.x + particle.vx * 8.0
            y2 = particle.y + particle.vy * 8.0
            self.canvas.create_line(
                particle.x,
                particle.y,
                x2,
                y2,
                fill=VELOCITY,
                width=1,
                arrow=tk.LAST,
                arrowshape=(8, 10, 3),
            )

    def _draw_flashes(self) -> None:
        for flash in self.flashes:
            fraction = flash.life / max(1, flash.max_life)
            radius = 2 + 4 * fraction
            self.canvas.create_oval(
                flash.x - radius,
                flash.y - radius,
                flash.x + radius,
                flash.y + radius,
                outline=flash.color,
                fill="",
                width=2,
            )
            self.canvas.create_text(flash.x + 8, flash.y - 8, text=flash.label, fill=flash.color, font=(FONT, 8, "bold"))

    def _draw_particles(self) -> None:
        for i, particle in enumerate(self.particles):
            radius = particle.radius + (2 if i == self.dragged_index else 0)
            if i == self.selected_index:
                self.canvas.create_oval(
                    particle.x - radius - 6,
                    particle.y - radius - 6,
                    particle.x + radius + 6,
                    particle.y + radius + 6,
                    outline="#ffffff",
                    width=1,
                    dash=(4, 3),
                )
            self.canvas.create_oval(
                particle.x - radius,
                particle.y - radius,
                particle.x + radius,
                particle.y + radius,
                fill=particle.fill,
                outline=particle.outline,
                width=2,
            )
            if particle.kind == PROTON:
                self.canvas.create_line(particle.x - 4, particle.y, particle.x + 4, particle.y, fill="white", width=2)
                self.canvas.create_line(particle.x, particle.y - 4, particle.x, particle.y + 4, fill="white", width=2)
            elif particle.kind == ELECTRON:
                self.canvas.create_line(particle.x - 3, particle.y, particle.x + 3, particle.y, fill="#191b1f", width=2)
            else:
                self.canvas.create_line(particle.x - 4, particle.y, particle.x + 4, particle.y, fill="white", width=2)

            if self.spin_labels_enabled.get():
                self.canvas.create_text(
                    particle.x + 12,
                    particle.y + 8,
                    text=particle.spin_symbol,
                    fill=particle.spin_color,
                    font=(FONT, 9, "bold"),
                )
            if self.labels_enabled.get():
                self.canvas.create_text(
                    particle.x,
                    particle.y - 18,
                    text=particle.label,
                    fill="#f7f7f2",
                    font=(FONT, 8, "bold"),
                )

    def update_stats(self) -> None:
        protons = sum(1 for particle in self.particles if particle.kind == PROTON)
        neutrons = sum(1 for particle in self.particles if particle.kind == NEUTRON)
        electrons = sum(1 for particle in self.particles if particle.kind == ELECTRON)
        spin_up = sum(1 for particle in self.particles if particle.spin == SPIN_UP)
        spin_down = len(self.particles) - spin_up
        kinetic, potential, total = self.compute_energy_parts()
        if self.running or not self.energy_history:
            self.energy_history.append((kinetic, potential, total))
            if len(self.energy_history) > 160:
                del self.energy_history[0]
        self.count_value.set(f"양성자: {protons}   중성자: {neutrons}   전자: {electrons}   전체: {len(self.particles)}")
        self.quantum_value.set(
            f"스핀 ↑ {spin_up} / ↓ {spin_down}   파울리: {self.pauli_contact_count}   "
            f"베타: {self.decay_count}   융합: {self.fusion_count}   분열: {self.fission_count}"
        )
        self.energy_value.set(f"운동 {kinetic:.2f} | 위치 {potential:.2f} | 전체 {total:.2f} | 단계 {self.step_count}")
        self.update_selection_info()

    def update_selection_info(self) -> None:
        if self.selected_index is None or self.selected_index < 0 or self.selected_index >= len(self.particles):
            self.selected_index = None
            self.selection_value.set("선택: 없음")
            self.selection_detail_value.set("입자를 클릭하면 세부 정보가 표시돼")
            return
        particle = self.particles[self.selected_index]
        speed = math.hypot(particle.vx, particle.vy)
        neighbors = self._local_neighbor_counts(particle)
        cluster_size = self._selected_cluster_size(self.selected_index)
        self.selection_value.set(f"선택: {particle.korean_name}{particle.spin_symbol}  #{self.selected_index}")
        self.selection_detail_value.set(
            f"전하 {particle.charge:+.0f}, 질량 {particle.mass:.3f}, 속도 {speed:.2f}, "
            f"주변 핵자 {neighbors[0]}, 주변 전자 {neighbors[1]}, 클러스터 {cluster_size}"
        )

    def _local_neighbor_counts(self, target: Particle) -> tuple[int, int]:
        nucleons = 0
        electrons = 0
        limit = max(32.0, self.strong_range.get() * 1.25)
        for particle in self.particles:
            if particle is target:
                continue
            if math.hypot(particle.x - target.x, particle.y - target.y) > limit:
                continue
            if self._is_nucleon(particle):
                nucleons += 1
            elif particle.kind == ELECTRON:
                electrons += 1
        return nucleons, electrons

    def _selected_cluster_size(self, index: int) -> int:
        if index < 0 or index >= len(self.particles) or not self._is_nucleon(self.particles[index]):
            return 0
        for component in self._nucleon_components():
            if index in component:
                return len(component)
        return 1

    def compute_energy_parts(self) -> tuple[float, float, float]:
        kinetic = sum(0.5 * p.mass * (p.vx * p.vx + p.vy * p.vy) for p in self.particles)
        potential = 0.0
        for i, a in enumerate(self.particles):
            for b in self.particles[i + 1 :]:
                r = max(MIN_DISTANCE, math.hypot(b.x - a.x, b.y - a.y))
                if self.strong_enabled.get() and self._is_nucleon(a) and self._is_nucleon(b):
                    potential += self._strong_potential(r)
                if self.electric_enabled.get() and a.charge and b.charge:
                    potential += self._electric_potential(a.charge, b.charge, r)
                    if self._is_electron_nucleus_pair(a, b):
                        potential += self.electron_core_strength.get() * 16.0 * math.exp(-((r / 16.0) ** 2))
                if self.pauli_enabled.get() and self._same_quantum_bucket(a, b):
                    potential += self._pauli_potential(r)
        return kinetic, potential, kinetic + potential

    def _draw_energy_history(self) -> None:
        if not hasattr(self, "energy_canvas"):
            return
        canvas = self.energy_canvas
        canvas.delete("all")
        width = max(20, canvas.winfo_width())
        height = max(20, canvas.winfo_height())
        canvas.create_text(6, 5, text="빨강 운동 / 파랑 위치 / 노랑 전체", anchor="nw", fill="#60646c", font=(FONT, 7))
        if len(self.energy_history) < 2:
            return

        values = [value for triplet in self.energy_history for value in triplet]
        minimum = min(values)
        maximum = max(values)
        if abs(maximum - minimum) < 0.001:
            maximum = minimum + 1.0

        if minimum < 0 < maximum:
            zero_y = self._scale_energy(0.0, minimum, maximum, height)
            canvas.create_line(4, zero_y, width - 4, zero_y, fill="#d9d6ce")

        for index, color in ((0, "#e84855"), (1, "#247ba0"), (2, "#f2c14e")):
            points: list[float] = []
            for i, triplet in enumerate(self.energy_history):
                x = i / max(1, len(self.energy_history) - 1) * (width - 8) + 4
                y = self._scale_energy(triplet[index], minimum, maximum, height)
                points.extend((x, y))
            canvas.create_line(*points, fill=color, width=2, smooth=True)

    def _scale_energy(self, value: float, minimum: float, maximum: float, height: int) -> float:
        top = 18
        bottom = height - 5
        ratio = (value - minimum) / (maximum - minimum)
        return bottom - ratio * (bottom - top)


def main() -> None:
    root = tk.Tk()
    NucleonSimulator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
