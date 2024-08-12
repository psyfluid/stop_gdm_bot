import sys
import pymorphy2
import spacy


def decline_phrase_in_all_cases(phrase, dataset_size):
    nlp = spacy.load(f'ru_core_news_{dataset_size}')
    doc = nlp(phrase)
    declined_phrases = []

    cases = [
        'nomn',
        'gent',
        'datv',
        'accs',
        'ablt',
        'loct',
        'voct',
        'gen1',
        'gen2',
        'acc2',
        'loc1',
        'loc2']

    for case in cases:
        declined_phrase_parts = []
        for token in doc:
            if token.pos_ in ["NOUN", "ADJ"]:
                parsed = pymorphy2.MorphAnalyzer().parse(token.text)[0]
                # Check for irregular forms and handle them appropriately
                if case in ['gent', 'datv', 'accs', 'ablt', 'loct',
                            'voct', 'gen1', 'gen2', 'acc2', 'loc1', 'loc2']:
                    declined_form = parsed.inflect({case})
                    if declined_form:
                        declined_phrase_parts.append(declined_form.word)
                    else:
                        # Handle irregular forms or fallback to base form
                        declined_phrase_parts.append(parsed.normal_form)
                else:
                    # For nominative case, use the normal form
                    declined_phrase_parts.append(parsed.normal_form)
            else:
                # For non-declinable words, just append them as they are
                declined_phrase_parts.append(token.text)

        declined_phrases.append(' '.join(declined_phrase_parts))

    return declined_phrases


def main(input_file_path, output_file_path, dataset_size):
    try:
        with open(input_file_path, 'r', encoding='utf-8') as infile:
            phrases = infile.readlines()

        declined_phrases_all_cases = []
        for phrase in phrases:
            declined_phrases = decline_phrase_in_all_cases(phrase.strip(), dataset_size)
            declined_phrases_all_cases.append(declined_phrases)

        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            for declined_phrases in declined_phrases_all_cases:
                outfile.write('\n'.join(declined_phrases) + '\n\n')

        print(f"Processed phrases. Results written to {output_file_path}.")

    except FileNotFoundError:
        print("Input file not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python decline_phrases_all_cases.py <input_file_path> <output_file_path> <dataset_size>")
        sys.exit(1)

    input_file_path = sys.argv[1]
    output_file_path = sys.argv[2]
    dataset_size = sys.argv[3]

    main(input_file_path, output_file_path, dataset_size)
