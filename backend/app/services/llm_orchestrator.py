"""LLM Orchestrator -- pluggable LLM backend: Claude -> GPT-4o -> Phi-3-mini."""

from app.config import settings


class LLMOrchestrator:
    """Orchestrate LLM calls with fallback chain."""

    def __init__(self, provider: str | None = None):
        self.provider = provider or settings.llm_provider

    def _call_claude(self, prompt: str, system: str = "") -> str:
        """Call Claude API (primary)."""
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        default_sys = (
            "You are a helpful travel packing advisor. Be concise and practical."
        )
        message = client.messages.create(
            model=settings.providers["claude"]["model"],
            max_tokens=settings.providers["claude"]["max_tokens"],
            system=system or default_sys,
            messages=[{"role": "user", "content": prompt}],
            temperature=settings.providers["claude"]["temperature"],
        )
        return message.content[0].text

    def _call_openai(self, prompt: str, system: str = "") -> str:
        """Call GPT-4o (fallback)."""
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        default_sys = (
            "You are a helpful travel packing advisor. Be concise and practical."
        )
        response = client.chat.completions.create(
            model=settings.providers["openai"]["model"],
            messages=[
                {"role": "system", "content": system or default_sys},
                {"role": "user", "content": prompt},
            ],
            max_tokens=settings.providers["openai"]["max_tokens"],
            temperature=settings.providers["openai"]["temperature"],
        )
        return response.choices[0].message.content

    def _call_local(self, prompt: str, system: str = "") -> str:
        """Call local Phi-3-mini via llama.cpp (offline fallback)."""
        from llama_cpp import Llama

        llm = Llama(
            model_path=settings.providers["local"]["model_path"],
            n_ctx=settings.providers["local"]["n_ctx"],
            n_gpu_layers=settings.providers["local"]["n_gpu_layers"],
        )
        if system:
            full_prompt = f"{system}\n\nUser: {prompt}\n\nAssistant:"
        else:
            full_prompt = f"User: {prompt}\n\nAssistant:"
        local_cfg = settings.providers["local"]
        output = llm(
            full_prompt,
            max_tokens=local_cfg["max_tokens"],
            temperature=local_cfg["temperature"],
        )
        return output["choices"][0]["text"].strip()

    def generate(self, prompt: str, system: str = "") -> str:
        """Generate LLM response with fallback chain."""
        chain = {
            "claude": [self._call_claude, self._call_openai, self._call_local],
            "openai": [self._call_openai, self._call_claude, self._call_local],
            "local": [self._call_local, self._call_claude, self._call_openai],
        }
        methods = chain.get(self.provider, chain["claude"])

        for method in methods:
            try:
                result = method(prompt, system)
                if result and not result.startswith("__ERROR__"):
                    return result
            except Exception:
                continue

        return (
            "Unable to generate AI advice at this time. "
            "Please refer to the packing list and weather recommendations."
        )

    def generate_packing_advice(
        self,
        destination: str,
        trip_duration_days: int,
        activity_type: str,
        weather_summary: dict,
        airline_summary: dict,
    ) -> str:
        """Generate natural-language packing advice for a trip."""
        prompt = (
            f"I'm traveling to {destination} for {trip_duration_days} days "
            f"({activity_type} trip).\n\n"
            f"Weather forecast:\n"
            f"- Average high: {weather_summary.get('avg_temp_max_c', 'N/A')} C\n"
            f"- Average low: {weather_summary.get('avg_temp_min_c', 'N/A')} C\n"
            f"- Max precipitation probability: "
            f"{weather_summary.get('max_precip_probability', 0)}%\n"
            f"- Max UV index: {weather_summary.get('max_uv_index', 0)}\n\n"
            f"Airline: {airline_summary.get('airline', 'N/A')} "
            f"({airline_summary.get('iata_code', 'N/A')})\n"
            f"Checked bag limit: "
            f"{airline_summary.get('checked', {}).get('weight_kg', 23)} kg\n\n"
            f"Please provide:\n"
            f"1. 3 destination-specific packing tips\n"
            f"2. Any items I might forget\n"
            f"3. Smart substitution suggestions to save weight/space\n"
            f"4. Customs or local restrictions I should know about"
        )
        return self.generate(prompt)

    def generate_customs_alert(self, destination: str, origin: str = "US") -> str:
        """Check for customs-restricted items at destination."""
        prompt = (
            f"What items are restricted or prohibited by customs "
            f"when traveling from {origin} to {destination}? "
            f"Focus on: food, medications, electronics, drones, "
            f"publications, and culturally sensitive items. "
            f"Be concise -- list only the most important restrictions."
        )
        return self.generate(prompt)

    def generate_smart_substitutions(self, items: list[dict]) -> str:
        """Suggest lighter alternatives for heavy items."""
        heavy_items = [i for i in items if (i.get("weight_grams", 0) or 0) > 300]
        if not heavy_items:
            return "No heavy items that need substitution."

        item_descriptions = "\n".join(
            f"- {i['name']} ({i.get('weight_grams', 0)}g)" for i in heavy_items
        )
        prompt = (
            f"Suggest lighter travel alternatives for these heavy items:\n"
            f"{item_descriptions}\n"
            f"For each item, suggest a travel-size or compact "
            f"alternative with estimated weight savings."
        )
        return self.generate(prompt)


llm_orchestrator = LLMOrchestrator()
