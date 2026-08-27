import math

class NaturalLanguageMetrics:
    def __init__(self, beta=1.0):
        self.beta = beta

class Bleu(NaturalLanguageMetrics):
    def _calculate_ngram(self, string, n):
        ngram = {}
        for i in range(0, len(string) - n + 1):
            g = " ".join(string[i:i + n])
            ngram[g] = ngram.get(g, 0) + 1
        return ngram

    def _calculate_ngram_modified_precision(self, candidate, references, n):
        # Calculate n-gram count for candidate
        clipped_count = {}
        candidate_ngram = self._calculate_ngram(candidate, n)
        for ngram in candidate_ngram.keys():
            clipped_count[ngram] = min(candidate_ngram[ngram], max([reference.count(ngram) for reference in references]))

        # Calculate clipped counts
        clipped_counts = sum(clipped_count.values())

        # Calculate precision
        precision = float(clipped_counts) / float(max(1, sum(candidate_ngram.values())))

        return precision

    def _calculate_brevity_penalty(self, candidate, references):
        # Calculate brevity penalty
        c = len(candidate)
        r = min([abs(len(candidate) - len(reference)) for reference in references])
        if c > r:
            brevity_penalty = 1
        else:
            brevity_penalty = math.exp(1 - float(r) / float(c))
        return brevity_penalty

    def evaulate(self, output, target):
        assert (len(output) == 1)
        assert (len(target) > 0)
        precisions = []
        for i in range(1, self.n + 1):
            precisions.append(self._calculate_ngram_modified_precision(output[0].split(" "), target, i))
        brevity_penalty = self._calculate_brevity_penalty(output[0].split(" "), target)
        score = brevity_penalty * math.exp(sum([math.log(p) for p in precisions]) / float(self.n))
        return score

class Rouge(NaturalLanguageMetrics):
    def _calculate_longest_common_subsequence(self, string, sub):
        if len(string) < len(sub):
            sub, string = string, sub

        lengths = [[0 for i in range(0, len(sub) + 1)] for j in range(0, len(string) + 1)]

        for j in range(1, len(sub) + 1):
            for i in range(1, len(string) + 1):
                if string[i - 1] == sub[j - 1]:
                    lengths[i][j] = lengths[i - 1][j - 1] + 1
                else:
                    lengths[i][j] = max(lengths[i - 1][j], lengths[i][j - 1])

        return lengths[len(string)][len(sub)]
        
    def evaulate(self, output, reference):
        # Split into tokens
        token_c = output.split(" ")
        token_r = reference.split(" ")

        # Compute the longest common subsequence
        lcs = self._calculate_longest_common_subsequence(token_r, token_c)

        # Calculate precision and recall
        prec = lcs / float(len(token_c))
        rec = lcs / float(len(token_r))

        # Calculate F1-score
        if prec + rec != 0:  # Check to avoid division by zero
            f1_score = 2 * prec * rec / (prec + rec)
        else:
            f1_score = 0.0

        return f1_score

