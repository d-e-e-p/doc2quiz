

example_yaml = """---
questions:
  items:
    - type: matching
      title: Match letters
      prompt: Match the following terms with their definitions.
      points: 1
      pairs:
        - key: Term A
          value: Definition A
          explanation: feedback on getting A wrong
        - key: Term B
          value: Definition B
          explanation: feedback on getting B wrong
      explanation: general feedback on this problem
      quotes:
        - start_ptr: 21
          end_ptr: 27
          text: A is A
        - start_ptr: 33
          end_ptr: 39
          text: B is B


    - type: multiple_answers
      title: Programming Languages
      prompt: Which of the following are programming languages?
      points: 2
      options:
        - option: Python
          explanation: Python is a popular high-level language 
          answer: true
        - option: Java
          explanation: Java is a widely-used object-oriented language.
          answer: true
        - option: HTML
          explanation: HTML is a markup language. 
        - option: CSS
          explanation: CSS is a style sheet language.
      explanation: Python/Java are languages
      quotes:
        - start_ptr: 99
          end_ptr: 124
          text: Python/Java are languages
        - start_ptr: 150
          end_ptr: 176
          text: HTML/CSS are not languages

    - type: multiple_choice
      title: Capitals
      prompt: What is the capital of Japan?
      points: 1
      options:
        - option: Seoul
          explanation: Seoul is the capital of South Korea.
        - option: Tokyo
          explanation: Tokyo is the correct answer. It is the capital of Japan.
          answer: true
        - option: Beijing
          explanation: Beijing is the capital of China.
        - option: Bangkok
          explanation: Bangkok is the capital of Thailand.
      explanation: Tokyo is the capital of Japan
      quotes:
        - start_ptr: 181
          end_ptr: 105
          text: Japan's capital is Tokyo 

    - type: multiple_dropdowns
      title: Capitals
      prompt: The capital of [blank1] is [blank2]
      points: 1
      dropdowns:
        - dropdown: blank1
          options:
            - option: France
              explanation: France is incorrect
            - option: India
              answer: true
              explanation: Delhi is the capital of India
            - option: Singapore
              explanation: Singapore is incorrect
        - dropdown: blank2
          options:
            - option: Delhi
              answer: true
              explanation: Delhi is the capital of India
            - option: Berlin
              explanation: Berlin is incorrect.
            - option: Rome
              explanation: Rome is incorrect.
      explanation: Berlin is capital of Germany
      quotes:
        - start_ptr: 234
          end_ptr: 262
          text: Berlin is capital of Germany

    - type: short_answer
      title: Color
      prompt: What is the opposite of black?
      points: 1
      answers:
        - White
        - white
      explanation: Opposite of black is white
      quotes:
        - start_ptr: 452
          end_ptr: 481
          text: black and white are opposites

    - type: true_false
      title: The Sun
      prompt: The sun rises in the west.
      points: 1
      answer: false
      explanation: The sun rises in the east, not the west.
      quotes:
        - start_ptr: 799
          end_ptr: 820
          text: Sun rises in the west
"""
