
import re


def create_study_plan(hours, topics):
    """Divide available study time equally among topics."""

    # Validate study hours
    if hours <= 0:
        return "Please enter a positive number of hours."

    # Validate subjects
    if not topics:
        return "Please enter at least one subject."

    total_minutes = round(hours * 60)
    minutes_each = total_minutes // len(topics)
    remaining = total_minutes % len(topics)

    print("\n===== YOUR STUDY PLAN =====")
    print(f"Total study time: {total_minutes} minutes\n")

    start = 0

    for i, topic in enumerate(topics):
        duration = minutes_each + (1 if i < remaining else 0)
        end = start + duration

        print(
            f"{start // 60:02d}:{start % 60:02d} - "
            f"{end // 60:02d}:{end % 60:02d} | "
            f"{topic} ({duration} minutes)"
        )

        start = end

    print("\nTip: Take short breaks between subjects!")
    return "Study plan created successfully."


def main():
    print("Study Planner - Free Local Version")
    print("Type 'exit' to stop.")

    while True:
        question = input("\nYou: ").strip()

        # Exit the program
        if question.lower() == "exit":
            print("Good luck with your studies!")
            break

        # Handle empty input
        if not question:
            print("Please enter a question.")
            continue

        # Extract numeric study hours
        match = re.search(
            r"(\d+(?:\.\d+)?)\s*hours?",
            question,
            re.IGNORECASE
        )

        if not match:
            print(
                "Please mention study time using a number, "
                "for example: 2 hours."
            )
            continue

        # Convert hours safely
        try:
            hours = float(match.group(1))
        except ValueError:
            print("Please enter a valid number of hours.")
            continue

        # Reject zero or negative hours
        if hours <= 0:
            print("Study hours must be greater than zero.")
            continue

        # Find subjects after the word 'study'
        topic_match = re.search(
            r"\bstudy\s+(.+)",
            question,
            re.IGNORECASE
        )

        if not topic_match:
            print(
                "Please mention subjects after the word "
                "'study', for example: study Java and SQL."
            )
            continue

        # Remove punctuation after the subject list
        topic_text = re.split(
            r"[.!?]",
            topic_match.group(1)
        )[0]

        # Convert 'and' into a comma separator
        topic_text = re.sub(
            r"\s+and\s+",
            ",",
            topic_text,
            flags=re.IGNORECASE
        )

        # Create a list of subjects
        topics = [
            topic.strip()
            for topic in topic_text.split(",")
            if topic.strip()
        ]

        # Validate subjects
        if not topics:
            print("Please enter at least one subject.")
            continue

        # Generate the study plan
        try:
            result = create_study_plan(hours, topics)
            print(result)
        except Exception as error:
            print("Something went wrong:", error)


if __name__ == "__main__":
    main()
