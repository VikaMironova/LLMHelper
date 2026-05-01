import json
import random
import re
from chat_model.questions_bank import QUESTIONS_BANK_JUNIOR, QUESTIONS_BANK_MIDDLE, QUESTIONS_BANK_SENIOR
from langchain_ollama import OllamaLLM

llm_view = OllamaLLM(model="llama3.1:8b", temperature=0.5)

QUESTIONS_BANK = {
    "junior": QUESTIONS_BANK_JUNIOR,
    "middle": QUESTIONS_BANK_MIDDLE,
    "senior": QUESTIONS_BANK_SENIOR,
}

levels = list(QUESTIONS_BANK.keys())
for i, level in enumerate(levels, 1):
    print(f"{i} - {level}")
ask_me = int(input("Пожалуйста, выберите уровень сложности (1-3): "))
prole = levels[ask_me - 1]

titles = list(QUESTIONS_BANK[prole].keys())
for i, title in enumerate(titles, 1):
    print(f"{i} - {title}")
ask_me_1 = int(input("Пожалуйста, выберите тему (1-4): "))
prole_1 = titles[ask_me_1 - 1]

print("Сколько вопросов хотите?")
print("1 - 3 вопроса (быстрое)")
print("2 - 5 вопросов (среднее)")
print("3 - 10 вопросов (полное)")

q_choice = int(input("Ваш выбор (1-3): "))

if q_choice == 1:
    num_questions = 3
elif q_choice == 2:
    num_questions = 5
else:
    num_questions = 10

all_questions = QUESTIONS_BANK[prole][prole_1]
select_questions = random.sample(all_questions, min(num_questions, len(all_questions)))

print(f"Подготовлено {len(select_questions)} вопроса(-ов) уровень {prole} по теме {prole_1}")

answers_history = []

for i, question in enumerate(select_questions, 1):
    print(f"\nВопрос {i}/{len(select_questions)}:")
    print(f"{question}\n")
    user_answer = input("Ваш ответ: ")

    answers_history.append({
        "question": question,
        "answer": user_answer,
        "question_number": i
    })

print("Все ответы собраны. Проверяю...")


def evaluate_all_answers(level: str, title: str, answers: list) -> dict:
    """
    Отправляет ВСЕ ответы пользователя одним запросом в LLM
    """
    questions_text = ""
    for a in answers:
        questions_text += f"""
        ### Вопрос {a['question_number']}:
        {a['question']}
        
        ### Ответ кандидата на вопрос {a['question_number']}:
        {a['answer']}

    """
    prompt = f"""
        Ты — строгий технический интервьюер.
        
        Уровень сложности: {level}
        Тема: {title}
        
        Ниже представлены ВСЕ вопросы и ответы кандидата:
        
        {questions_text}
        
        Оцени ответы кандидата. Верни ТОЛЬКО JSON в точном формате:
        {{
            "total_summary": {{
                "average_score": число от 0 до 10,
                "final_verdict": "короткий вердикт (готов/почти готов/не готов)",
                "overall_feedback": "общее впечатление о кандидате (2-3 предложения)",
                "strong_points": ["список сильных сторон"],
                "weak_points": ["список слабых мест"]
            }},
            "question_results": [
                {{
                    "question_number": 1,
                    "score": число от 0 до 10,
                    "feedback": "короткий фидбек по этому ответу (1 предложение)",
                    "what_is_good": "что хорошо в этом ответе",
                    "what_to_improve": "что улучшить"
                }},
                ... и так для каждого вопроса
            ]
        }}
        
        Не пиши ничего кроме JSON!
    """

    try:
        response = llm_view.invoke(prompt)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return result
        else:
            return {
                "total_summary": {
                    "average_score": 5,
                    "final_verdict": "Ошибка разбора",
                    "overall_feedback": "Не удалось получить оценку от LLM",
                    "strong_points": [],
                    "weak_points": []
                },
                "question_results": [
                    {
                        "question_number": a["question_number"],
                        "score": 5,
                        "feedback": "Ошибка оценки",
                        "what_is_good": "-",
                        "what_to_improve": "Попробуйте структурировать ответ"
                    } for a in answers
                ]
            }
    except Exception as e:
        return {
            "total_summary": {
                "average_score": 5,
                "final_verdict": "Ошибка",
                "overall_feedback": f"Ошибка: {e}",
                "strong_points": [],
                "weak_points": []
            },
            "question_results": [
                {
                    "question_number": a["question_number"],
                    "score": 5,
                    "feedback": f"Ошибка: {e}",
                    "what_is_good": "-",
                    "what_to_improve": "Попробуйте ещё раз"
                } for a in answers
            ]
        }

evaluation = evaluate_all_answers(prole, prole_1, answers_history)

for q_result in evaluation.get("question_results", []):

    q_num = q_result.get("question_number")
    score = q_result.get("score", 5)
    feedback = q_result.get("feedback", "")
    what_is_good = q_result.get("what_is_good", "")
    what_to_improve = q_result.get("what_to_improve", "")

    question_text = next((a["question"] for a in answers_history if a["question_number"] == q_num), "")

    if score >= 8:
        score_symbol = "🟢"
    elif score >= 5:
        score_symbol = "🟡"
    else:
        score_symbol = "🔴"

    print(f"\n--- Вопрос {q_num} ---")
    print(f"Вопрос: {question_text[:100]}...")
    print(f"{score_symbol} Оценка: {score}/10")

    if feedback:
        print(f"Фидбек: {feedback}")
    if what_is_good:
        print(f"Хорошо: {what_is_good}")
    if what_to_improve:
        print(f"Улучшить: {what_to_improve}")


total_summary = evaluation.get("total_summary", {})
average_score = total_summary.get("average_score", 0)
final_verdict = total_summary.get("final_verdict", "")
overall_feedback = total_summary.get("overall_feedback", "")
strong_points = total_summary.get("strong_points", [])
weak_points = total_summary.get("weak_points", [])

print(f"\nСредний балл: {average_score:.1f}/10")
print(f"Вердикт: {final_verdict}")
print(f"\nОбщее впечатление: {overall_feedback}")

if strong_points:
    print(f"\nСильные стороны:")
    for point in strong_points:
        print(f"   • {point}")

if weak_points:
    print(f"\nСлабые места:")
    for point in weak_points:
        print(f"   • {point}")

if average_score >= 8:
    print("\nВы готовы к реальному собеседованию!")
    print("Вы показали отличные знания! Смело идите на интервью.")
elif average_score >= 6:
    print("\nВы почти готовы, но нужно подтянуть")
    print("Повторите темы и попробуйте ещё раз.")
else:
    print("\nВы не готовы, нужно серьёзно подтянуть теорию")
    print("Рекомендуем изучить указанные темы и пройти тренировку заново.")

print("\nСобеседование завершено!")
