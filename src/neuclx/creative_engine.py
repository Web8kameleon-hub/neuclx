"""Stdlib-only creative engine with a deterministic SVG image generator."""

from __future__ import annotations

from typing import ClassVar
from dataclasses import dataclass
from hashlib import sha256
import random
from pathlib import Path
from typing import Any

from .audio_adapter import AudioGenerator
from .code_adapter import CodeGenerator
from .creative_guard import JonaCreativeGuard
from .creative_tensor import CreativeModality, CreativeTensor
from .evidence import Datum, EvidenceState
from .three_d_adapter import CADGenerator
from .video_adapter import VideoGenerator


@dataclass(slots=True)
class CreativeResult:
    status: str
    modality: str
    conclusion: str
    tensor: dict[str, Any]
    evidence_chain: list[dict[str, Any]]
    ledger: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "modality": self.modality,
            "conclusion": self.conclusion,
            "tensor": self.tensor,
            "evidence_chain": self.evidence_chain,
            "ledger": self.ledger,
        }


class ImageGenerator:
    """Creates a deterministic SVG artifact from prompt and seed."""

    def __init__(self, output_dir: str = "data/creative_outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, prompt: str, *, seed: int = 42, style: str = "clean", author: str | None = None, **kwargs: Any) -> tuple[str, str]:
        key = sha256(f"{prompt}|{seed}|{style}|{author or ''}".encode()).hexdigest()[:12]
        output_path = self.output_dir / f"creative_{key}.svg"
        svg_text = self._build_svg(prompt=prompt, seed=seed, style=style, author=author, extra=kwargs)
        output_path.write_text(svg_text, encoding="utf-8")
        output_hash = sha256(svg_text.encode("utf-8")).hexdigest()
        return str(output_path), output_hash

    def _build_svg(self, *, prompt: str, seed: int, style: str, author: str | None, extra: dict[str, Any]) -> str:
        palette = self._palette(seed)
        accent = self._accent(seed)
        words = [word for word in prompt.split() if word]
        label = " ".join(words[:6]) if words else "Neurosonic Creative"
        subtitle = f"seed={seed} style={style}" + (f" author={author}" if author else "")
        extra_hint = ", ".join(f"{key}={value}" for key, value in sorted(extra.items()) if value is not None)
        if extra_hint:
            subtitle = f"{subtitle} {extra_hint}"

        circles = []
        for index in range(5):
            x = 60 + index * 110
            y = 120 + ((seed + index * 17) % 80)
            radius = 24 + (seed + index * 7) % 18
            circles.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{palette[index % len(palette)]}" opacity="0.86" />')

        bars = []
        for index, value in enumerate((seed % 7 + 1, seed % 5 + 2, seed % 3 + 3)):
            bars.append(f'<rect x="{100 + index * 140}" y="{290 - value * 18}" width="70" height="{value * 18}" rx="8" fill="{accent}" opacity="0.78" />')

        return (
            '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="420" viewBox="0 0 800 420" role="img" aria-labelledby="title desc">'
            f'<title>{self._escape(label)}</title>'
            f'<desc>{self._escape(prompt)}</desc>'
            f'<rect width="800" height="420" fill="#10131f" />'
            f'<circle cx="660" cy="80" r="120" fill="{palette[0]}" opacity="0.18" />'
            f'<circle cx="140" cy="330" r="140" fill="{palette[1]}" opacity="0.15" />'
            f'<text x="40" y="54" fill="#f7f7fb" font-family="Georgia, serif" font-size="28" font-weight="700">{self._escape(label)}</text>'
            f'<text x="40" y="86" fill="#cfd6ff" font-family="Consolas, monospace" font-size="14">{self._escape(subtitle)}</text>'
            + "".join(circles)
            + "".join(bars)
            + '<rect x="40" y="340" width="720" height="42" rx="12" fill="#ffffff" opacity="0.05" />'
            + f'<text x="60" y="368" fill="#e8ecff" font-family="Consolas, monospace" font-size="12">prompt_hash={sha256(prompt.encode("utf-8")).hexdigest()[:16]}</text>'
            + f'<text x="60" y="390" fill="#e8ecff" font-family="Consolas, monospace" font-size="12">seed={seed} · style={self._escape(style)} · deterministic</text>'
            + '</svg>'
        )

    @staticmethod
    def _escape(value: str) -> str:
        return (
            value.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    @staticmethod
    def _palette(seed: int) -> list[str]:
        colors = ["#8dd3c7", "#ffffb3", "#bebada", "#fb8072", "#80b1d3"]
        shift = seed % len(colors)
        return colors[shift:] + colors[:shift]

    @staticmethod
    def _accent(seed: int) -> str:
        accents = ["#ffcf56", "#83e377", "#f78fb3", "#62d2ff", "#c792ea"]
        return accents[seed % len(accents)]


class TextGenerator:
    """Creates deterministic creative text with HVO-flavored metadata."""

    opening_lines: ClassVar[list[str]] = [
        "Në heshtje, sistemi i jep formë idesë.",
        "Çdo hap ruhet si gjurmë e verifikueshme.",
        "Prompt-i bëhet boshti i krijimit.",
        "HVO e mban strukturën të qartë dhe të lexueshme.",
    ]
    closing_lines: ClassVar[list[str]] = [
        "Provenanca mbetet e plotë dhe e kontrollueshme.",
        "JONA e mban daljen të lidhur me qëllimin.",
        "Krijimi nuk del jashtë kufijve të evidencës.",
        "Rezultati është i riprodhueshëm dhe i ruajtshëm.",
    ]

    def generate(self, prompt: str, *, seed: int = 42, style: str = "clean", author: str | None = None, max_words: int = 120, **kwargs: Any) -> tuple[str, dict[str, Any]]:
        rng = random.Random(sha256(f"{prompt}|{seed}|{style}|{author or ''}".encode()).hexdigest())
        words = [word.strip(".,:;!?()[]{}") for word in prompt.split() if word.strip(".,:;!?()[]{}")]
        key_words = self._top_keywords(words)
        opening = rng.choice(self.opening_lines)
        closing = rng.choice(self.closing_lines)
        lines = [
            f"{opening} Tema: {self._summarize(prompt, key_words)}.",
            f"Stili {style} e formon zërin me seed {seed} dhe autor {author or 'unknown'}.",
            f"Fjalët bosht: {', '.join(key_words) if key_words else 'pa fjalë bosht'}.",
            f"HVO profile: H={len(words)} V={len(key_words)} W={len(prompt)} A={len(author or '')}.",
            closing,
        ]
        output_text = "\n".join(lines)
        if max_words and len(output_text.split()) > max_words:
            output_text = " ".join(output_text.split()[:max_words])

        metadata = {
            "text": output_text,
            "model": "neuclx-creative-text",
            "seed": seed,
            "style": style,
            "author": author,
            "hvo_profile": {
                "H": len(words),
                "V": len(key_words),
                "W": len(prompt),
                "A": len(author or ""),
            },
            "keywords": key_words,
        }
        return output_text, metadata

    @staticmethod
    def _top_keywords(words: list[str]) -> list[str]:
        seen = []
        for word in words:
            lowered = word.casefold()
            if len(lowered) < 4 or lowered in seen:
                continue
            seen.append(lowered)
        return seen[:5]

    @staticmethod
    def _summarize(prompt: str, keywords: list[str]) -> str:
        if keywords:
            return ", ".join(keywords[:3])
        stripped = prompt.strip()
        return stripped[:80] if stripped else "Neurosonic"


class CreativeEngine:
    def __init__(self, memory_manager, output_dir: str = "data/creative_outputs"):
        self.memory = memory_manager
        self.guard = JonaCreativeGuard()
        self.image_generator = ImageGenerator(output_dir=output_dir)
        self.text_generator = TextGenerator()
        self.audio_generator = AudioGenerator(output_dir=output_dir)
        self.code_generator = CodeGenerator(output_dir=output_dir)
        self.video_generator = VideoGenerator(output_dir=output_dir)
        self.cad_generator = CADGenerator(output_dir=output_dir)

    @staticmethod
    def _normalize_modality(modality: str) -> CreativeModality:
        normalized = (modality or "").strip().casefold()
        aliases = {"3d": "cad", "three_d": "cad", "3-d": "cad"}
        normalized = aliases.get(normalized, normalized)
        return CreativeModality(normalized)

    def _persist_response(self, prompt_text: str, response_datum: Datum) -> dict[str, Any]:
        if hasattr(self.memory, "record"):
            return self.memory.record(prompt_text, response_datum)
        return {"status": "unavailable"}

    def _build_tensor(self, *, prompt_text: str, seed: int, modality: CreativeModality, model_name: str, safety_score: float, fidelity_score: float, output_hash: str, output_path: str | None, parameters: dict[str, Any]) -> CreativeTensor:
        return CreativeTensor(
            prompt=prompt_text,
            seed=seed,
            modality=modality,
            model_name=model_name,
            safety_score=safety_score,
            fidelity_score=fidelity_score,
            output_hash=output_hash,
            output_path=output_path,
            parameters=parameters,
            state=EvidenceState.DECLARED,
        )

    @staticmethod
    def _artifact_hash(*parts: Any) -> str:
        payload = "|".join(str(part) for part in parts)
        return sha256(payload.encode()).hexdigest()

    def create(self, prompt: str, modality: str = "text", **kwargs: Any) -> dict[str, Any]:
        prompt_text = (prompt or "").strip()
        if not prompt_text:
            raise ValueError("prompt is required")

        if not self.guard.check_prompt(prompt_text):
            return {"status": "rejected_prompt", "reason": "Prompt përmban përmbajtje të ndaluar."}

        normalized_modality = self._normalize_modality(modality)
        seed = int(kwargs.get("seed", 42))
        style = str(kwargs.get("style", "clean"))
        author = kwargs.get("author")
        generator_kwargs = {key: value for key, value in kwargs.items() if key not in {"seed", "style", "author"}}
        if normalized_modality is CreativeModality.TEXT:
            output_text, metadata = self.text_generator.generate(prompt_text, seed=seed, style=style, author=author, **generator_kwargs)
            safety_score = 1.0 if self.guard.check_prompt(prompt_text) else 0.0
            fidelity_score = self.guard.check_fidelity(prompt_text, output_text)
            tensor = self._build_tensor(
                prompt_text=prompt_text,
                seed=seed,
                modality=CreativeModality.TEXT,
                model_name="neuclx-creative-text",
                safety_score=safety_score,
                fidelity_score=fidelity_score,
                output_hash=sha256(output_text.encode("utf-8")).hexdigest(),
                output_path=None,
                parameters={**generator_kwargs, "style": style, "author": author},
            )
            response_datum = Datum(
                {
                    "modality": "text",
                    "output_text": output_text,
                    "output_hash": tensor.output_hash,
                    "seed": seed,
                    "style": style,
                    "model_name": tensor.model_name,
                    "safety_score": safety_score,
                    "fidelity_score": fidelity_score,
                },
                EvidenceState.DECLARED,
                source="creative_engine",
                method="creative:text",
                metadata={
                    "prompt": prompt_text,
                    "seed": seed,
                    "style": style,
                    "author": author,
                    "tensor": tensor.to_dict(),
                    "hvo_profile": metadata.get("hvo_profile", {}),
                    "keywords": metadata.get("keywords", []),
                    "evidence_chain": [
                        {"source": "prompt", "matching_terms": prompt_text.split()[:6], "score": 1.0},
                        {"source": "hvo", "matching_terms": list(metadata.get("hvo_profile", {}).keys()), "score": fidelity_score},
                    ],
                },
            )
            stored = self._persist_response(prompt_text, response_datum)
            return {
                "status": "ok",
                "modality": "text",
                "conclusion": "Creative text generated.",
                "output_text": output_text,
                "output_hash": tensor.output_hash,
                "safety_score": safety_score,
                "fidelity_score": fidelity_score,
                "tensor": tensor.to_dict(),
                "evidence_chain": response_datum.metadata.get("evidence_chain", []),
                "ledger": stored,
            }

        if normalized_modality is CreativeModality.IMAGE:
            output_path, output_hash = self.image_generator.generate(prompt_text, seed=seed, style=style, author=author, **generator_kwargs)
            svg_text = Path(output_path).read_text(encoding="utf-8")
            safety_score = self.guard.check_output_svg(svg_text, prompt_text)
            fidelity_score = self.guard.check_fidelity(prompt_text, svg_text)

            tensor = self._build_tensor(
                prompt_text=prompt_text,
                seed=seed,
                modality=CreativeModality.IMAGE,
                model_name="neuclx-svg-image-generator",
                safety_score=safety_score,
                fidelity_score=fidelity_score,
                output_hash=output_hash,
                output_path=output_path,
                parameters={k: v for k, v in kwargs.items() if v is not None},
            )

            response_datum = Datum(
                {
                    "modality": "image",
                    "output_path": output_path,
                    "output_hash": output_hash,
                    "seed": seed,
                    "style": style,
                    "model_name": tensor.model_name,
                    "safety_score": safety_score,
                    "fidelity_score": fidelity_score,
                },
                EvidenceState.DECLARED,
                source="creative_engine",
                method="creative:svg-image",
                metadata={
                    "prompt": prompt_text,
                    "seed": seed,
                    "style": style,
                    "author": author,
                    "tensor": tensor.to_dict(),
                    "evidence_chain": [
                        {"source": "prompt", "matching_terms": prompt_text.split()[:6], "score": 1.0},
                        {"source": "svg", "matching_terms": ["svg", "image"], "score": safety_score},
                    ],
                },
            )
            stored = self._persist_response(prompt_text, response_datum)
            return {
                "status": "ok",
                "modality": "image",
                "conclusion": "Creative image generated.",
                "output_path": output_path,
                "output_hash": output_hash,
                "safety_score": safety_score,
                "fidelity_score": fidelity_score,
                "tensor": tensor.to_dict(),
                "evidence_chain": response_datum.metadata.get("evidence_chain", []),
                "ledger": stored,
            }

        if normalized_modality is CreativeModality.AUDIO:
            output_path, output_hash, metadata = self.audio_generator.generate(prompt_text, seed=seed, style=style, author=author, **generator_kwargs)
            audio_guard_score = self.guard.check_output_file(output_path, "audio")
            safety_score = min(audio_guard_score, metadata.get("safety_score", 1.0))
            tensor = self._build_tensor(
                prompt_text=prompt_text,
                seed=seed,
                modality=CreativeModality.AUDIO,
                model_name=metadata.get("model_name", "neuclx-audio"),
                safety_score=safety_score,
                fidelity_score=metadata.get("fidelity_score", 0.9),
                output_hash=output_hash,
                output_path=output_path,
                parameters={**generator_kwargs, "style": style, "author": author},
            )
            response_datum = Datum(
                {
                    "modality": "audio",
                    "output_path": output_path,
                    "output_hash": output_hash,
                    "seed": seed,
                    "style": style,
                    "model_name": tensor.model_name,
                    "safety_score": safety_score,
                    "fidelity_score": tensor.fidelity_score,
                },
                EvidenceState.DECLARED,
                source="creative_engine",
                method="creative:audio",
                metadata={
                    "prompt": prompt_text,
                    "seed": seed,
                    "style": style,
                    "author": author,
                    "tensor": tensor.to_dict(),
                    "sample_rate": metadata.get("sample_rate"),
                    "duration": metadata.get("duration"),
                    "frequencies": metadata.get("frequencies", []),
                    "evidence_chain": [
                        {"source": "prompt", "matching_terms": prompt_text.split()[:6], "score": 1.0},
                        {"source": "wave", "matching_terms": ["wav", "audio"], "score": safety_score},
                    ],
                },
            )
            stored = self._persist_response(prompt_text, response_datum)
            return {
                "status": "ok",
                "modality": "audio",
                "conclusion": "Creative audio generated.",
                "output_path": output_path,
                "output_hash": output_hash,
                "safety_score": safety_score,
                "fidelity_score": tensor.fidelity_score,
                "tensor": tensor.to_dict(),
                "evidence_chain": response_datum.metadata.get("evidence_chain", []),
                "ledger": stored,
            }

        if normalized_modality is CreativeModality.CODE:
            output_path, output_hash, metadata = self.code_generator.generate(prompt_text, seed=seed, style=style, author=author, **generator_kwargs)
            code_guard_score = self.guard.check_output_file(output_path, "code")
            safety_score = min(code_guard_score, metadata.get("safety_score", 1.0))
            tensor = self._build_tensor(
                prompt_text=prompt_text,
                seed=seed,
                modality=CreativeModality.CODE,
                model_name=metadata.get("model_name", "neuclx-code"),
                safety_score=safety_score,
                fidelity_score=metadata.get("fidelity_score", 0.9),
                output_hash=output_hash,
                output_path=output_path,
                parameters={**generator_kwargs, "style": style, "author": author},
            )
            response_datum = Datum(
                {
                    "modality": "code",
                    "output_path": output_path,
                    "output_hash": output_hash,
                    "seed": seed,
                    "style": style,
                    "model_name": tensor.model_name,
                    "safety_score": safety_score,
                    "fidelity_score": tensor.fidelity_score,
                },
                EvidenceState.DECLARED,
                source="creative_engine",
                method="creative:code",
                metadata={
                    "prompt": prompt_text,
                    "seed": seed,
                    "style": style,
                    "author": author,
                    "tensor": tensor.to_dict(),
                    "language": metadata.get("language", "python"),
                    "function_name": metadata.get("function_name"),
                    "evidence_chain": [
                        {"source": "prompt", "matching_terms": prompt_text.split()[:6], "score": 1.0},
                        {"source": "code", "matching_terms": ["python", "function"], "score": safety_score},
                    ],
                },
            )
            stored = self._persist_response(prompt_text, response_datum)
            return {
                "status": "ok",
                "modality": "code",
                "conclusion": "Creative code generated.",
                "output_path": output_path,
                "output_hash": output_hash,
                "safety_score": safety_score,
                "fidelity_score": tensor.fidelity_score,
                "tensor": tensor.to_dict(),
                "evidence_chain": response_datum.metadata.get("evidence_chain", []),
                "ledger": stored,
            }

        if normalized_modality is CreativeModality.VIDEO:
            output_path, output_hash, metadata = self.video_generator.generate(prompt_text, seed=seed, style=style, author=author, **generator_kwargs)
            video_guard_score = self.guard.check_output_file(output_path, "video")
            safety_score = min(video_guard_score, metadata.get("safety_score", 1.0))
            tensor = self._build_tensor(
                prompt_text=prompt_text,
                seed=seed,
                modality=CreativeModality.VIDEO,
                model_name=metadata.get("model_name", "neuclx-video-package"),
                safety_score=safety_score,
                fidelity_score=metadata.get("fidelity_score", 0.9),
                output_hash=output_hash,
                output_path=output_path,
                parameters={**generator_kwargs, "style": style, "author": author},
            )
            response_datum = Datum(
                {
                    "modality": "video",
                    "output_path": output_path,
                    "output_hash": output_hash,
                    "seed": seed,
                    "style": style,
                    "model_name": tensor.model_name,
                    "safety_score": safety_score,
                    "fidelity_score": tensor.fidelity_score,
                },
                EvidenceState.DECLARED,
                source="creative_engine",
                method="creative:video",
                metadata={
                    "prompt": prompt_text,
                    "seed": seed,
                    "style": style,
                    "author": author,
                    "tensor": tensor.to_dict(),
                    "frame_count": metadata.get("frame_count"),
                    "frame_paths": metadata.get("frame_paths", []),
                    "evidence_chain": [
                        {"source": "prompt", "matching_terms": prompt_text.split()[:6], "score": 1.0},
                        {"source": "frames", "matching_terms": ["svg", "manifest", "video"], "score": safety_score},
                    ],
                },
            )
            stored = self._persist_response(prompt_text, response_datum)
            return {
                "status": "ok",
                "modality": "video",
                "conclusion": "Creative video package generated.",
                "output_path": output_path,
                "output_hash": output_hash,
                "safety_score": safety_score,
                "fidelity_score": tensor.fidelity_score,
                "tensor": tensor.to_dict(),
                "evidence_chain": response_datum.metadata.get("evidence_chain", []),
                "ledger": stored,
            }

        if normalized_modality is CreativeModality.CAD:
            output_path, output_hash, metadata = self.cad_generator.generate(prompt_text, seed=seed, style=style, author=author, **generator_kwargs)
            cad_guard_score = self.guard.check_output_file(output_path, "cad")
            safety_score = min(cad_guard_score, metadata.get("safety_score", 1.0))
            tensor = self._build_tensor(
                prompt_text=prompt_text,
                seed=seed,
                modality=CreativeModality.CAD,
                model_name=metadata.get("model_name", "neuclx-cad"),
                safety_score=safety_score,
                fidelity_score=metadata.get("fidelity_score", 0.9),
                output_hash=output_hash,
                output_path=output_path,
                parameters={**generator_kwargs, "style": style, "author": author},
            )
            response_datum = Datum(
                {
                    "modality": "cad",
                    "output_path": output_path,
                    "output_hash": output_hash,
                    "seed": seed,
                    "style": style,
                    "model_name": tensor.model_name,
                    "safety_score": safety_score,
                    "fidelity_score": tensor.fidelity_score,
                },
                EvidenceState.DECLARED,
                source="creative_engine",
                method="creative:cad",
                metadata={
                    "prompt": prompt_text,
                    "seed": seed,
                    "style": style,
                    "author": author,
                    "tensor": tensor.to_dict(),
                    "face_count": metadata.get("face_count"),
                    "vertex_count": metadata.get("vertex_count"),
                    "evidence_chain": [
                        {"source": "prompt", "matching_terms": prompt_text.split()[:6], "score": 1.0},
                        {"source": "obj", "matching_terms": ["obj", "mesh"], "score": safety_score},
                    ],
                },
            )
            stored = self._persist_response(prompt_text, response_datum)
            return {
                "status": "ok",
                "modality": "cad",
                "conclusion": "Creative 3D object generated.",
                "output_path": output_path,
                "output_hash": output_hash,
                "safety_score": safety_score,
                "fidelity_score": tensor.fidelity_score,
                "tensor": tensor.to_dict(),
                "evidence_chain": response_datum.metadata.get("evidence_chain", []),
                "ledger": stored,
            }

        return {
            "status": "not_implemented",
            "reason": f"Modality '{normalized_modality.value}' is not implemented yet.",
            "modality": normalized_modality.value,
        }


__all__ = ["CreativeEngine", "ImageGenerator", "TextGenerator"]