from app.agents.base import BaseExpert, ExpertConfig

# Weights bias horizon expertise. PM agent also re-weights downstream.
EXPERTS: list[BaseExpert] = [
    BaseExpert(ExpertConfig(
        name="buffett_munger",
        display="Buffett / Munger",
        prompt_file="buffett_munger",
        weight_day=0.6, weight_swing=0.9, weight_position=1.4,
    )),
    BaseExpert(ExpertConfig(
        name="dalio_druckenmiller",
        display="Dalio / Druckenmiller",
        prompt_file="dalio_druckenmiller",
        weight_day=0.9, weight_swing=1.1, weight_position=1.2,
    )),
    BaseExpert(ExpertConfig(
        name="ptj_schwartz",
        display="PTJ / Schwartz",
        prompt_file="ptj_schwartz",
        weight_day=1.5, weight_swing=1.3, weight_position=0.8,
    )),
    BaseExpert(ExpertConfig(
        name="burry_chanos",
        display="Burry / Chanos",
        prompt_file="burry_chanos",
        weight_day=0.9, weight_swing=1.0, weight_position=1.1,
    )),
]


def get_experts() -> list[BaseExpert]:
    return EXPERTS
