"""Domain routing for the V4.1 AI-video-only overlay."""


def is_ai_video_brief(brief):
    profile = str(brief.get("quality_profile", "")).strip().lower()
    if profile in {"ai_video_v4_1", "ai-video-v4.1", "ai_video_v4.1"}:
        return True
    domain = str(brief.get("domain", "")).strip().lower().replace("-", "_").replace(" ", "_")
    ai_domains = {"ai_video", "ai_video_business", "aivideo", "ai视频", "ai视频业务"}
    if domain:
        return domain in ai_domains
    line = brief.get("business_line", brief.get("business_lines", []))
    if isinstance(line, str):
        values = {x.strip().upper() for x in line.replace("+", ",").replace("/", ",").split(",")}
    elif isinstance(line, list):
        values = {str(x).strip().upper() for x in line}
    else:
        values = set()
    return bool(values & {"A", "B", "C"})
