import textdistance as td


# def match(resume, job_des):
#     j = td.jaccard.similarity(resume, job_des)
#     s = td.sorensen_dice.similarity(resume, job_des)
#     c = td.cosine.similarity(resume, job_des)
#     o = td.overlap.normalized_similarity(resume, job_des)
#     total = (j + s + c + o) / 4
#     return total

def match(resume, job_des):
    # Tokenize into words (simple whitespace split or use nltk.word_tokenize)
    resume_tokens = resume.lower().split()
    job_des_tokens = job_des.lower().split()

    j = td.jaccard.similarity(resume_tokens, job_des_tokens)
    s = td.sorensen_dice.similarity(resume_tokens, job_des_tokens)
    c = td.cosine.similarity(resume_tokens, job_des_tokens)
    o = td.overlap.normalized_similarity(resume_tokens, job_des_tokens)

    total = (j + s + c + o) / 4
    return total
