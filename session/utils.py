from django.conf import settings

import openai

from treatment_plan.models import TreatmentPlan


def generate_ai_suggestion(treatment_plan_id: int) -> str:
    """Generate a single AI suggestion question based on a treatment plan.

    Returns a human-readable suggestion string or an error message.
    """
    try:
        plan = TreatmentPlan.objects.get(pk=int(treatment_plan_id))
    except TreatmentPlan.DoesNotExist:
        return "Treatment plan not found."
    except Exception as exc:
        return f"AI error: {str(exc)}"

    goals = list(plan.goals.values_list('goal_description', flat=True))

    prompt = (
        f"Treatment Plan Type: {plan.plan_type}\n"
        f"Client: {plan.client_name}\n"
        f"Goals: {', '.join(goals) if goals else 'None'}\n\n"
        "Suggest one helpful, specific question a therapist should ask next for this client and treatment plan."
    )

    openai.api_key = getattr(settings, 'OPENAI_API_KEY', None)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert therapy suggestion AI."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as exc:
        return f"AI error: {str(exc)}"


