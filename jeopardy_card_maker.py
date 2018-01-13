from bs4 import BeautifulSoup
import requests
import re
import codecs
import json

with open('jeop_cfg') as f:
    jeop_cfg = json.load(f)

def game_categories(game_soup):
    '''Use BeautifulSoup to return a list of categories in the order they appear.'''
    soup_categories = game_soup.find_all("td", class_="category_name")
    category_list = [soup_categories[x].text for x in range(len(soup_categories))]
    return category_list

def game_questions_with_tags(game_soup):
    '''Use BeautifulSoup to return a list of questions (with tags) in the order they appear.  We need the tags for
    mapping the categories and values later.'''
    questions = game_soup.find_all("td", class_= "clue_text")
    return questions

def game_questions_text(game_soup):
    '''Return a list of pure questions text without html'''
    question_text = game_soup.find_all("td", class_= "clue_text")
    question_list = [question_text[x].text for x in range(len(question_text))]
    return question_list

def category_map(category_list):
    '''Loops through to map the formatting in the page source to the category.  Pass game_categories() as parameter.
    Leading underscore in passer variable prevents confusion between single and double jeopardy tags.'''
    i = 1
    j = 1
    pl = []
    while i < 7:
        passer = '_J_' + str(i) + '_'
        pl.append(passer)
        i += 1
    while j < 7:
        passer = '_DJ_' + str(j) + '_'
        pl.append(passer)
        j += 1
    d = dict(zip(pl, category_list))
    return d

def answers(game_soup):
    '''Use regex to find answers.  There are a couple different variations so two regex searches are needed plus
    a third for Final Jeopardy.  The for loop below the regex consolidates the two regex searches into one list
    by popping the first available value in m into n when n has a null string.  This works because everything is in
    proper order.'''
    k = str(game_soup)
    ans = re.findall(r'correct_response&quot;&gt;(.*?)&lt', k)
    ans_alt = re.findall(r'correct_response&quot;&gt;&lt;i&gt;(.*?)&lt', k)
    fja = re.findall(r'correct_response\\&quot;&gt;(.*?)&lt', k)
    fja_alt = re.findall(r'correct_response\\&quot;&gt;&lt;i&gt;(.*?)&lt', k)
    for i in range(len(ans)):
        z = ans[i]
        if z == '':
            ans[i] = ans_alt.pop(0)
    if fja[0] != '':
        ans.extend(fja)
    else:
        ans.extend(fja_alt)
    return ans

def final_jeopardy(gqt, game_cat):
    '''Take the last question from the question list, the last category, and return a tuple with 'FJ' difficulty.'''
    fjquestion = gqt[-1]
    fjcat = game_cat[-1]
    return (fjcat, 'FJ', fjquestion)

def parse_clue_value(questions, cat_map, fj):
    '''Use the categorymap function to see if the keys in categorymap() are in the question string.  If True,
     append a tuple with the category, the difficulty of the question (determined by the last character of j-archive
    format, i.e. J_1_1 is difficulty 1), and the question text.  Finally, append one last tuple for the FJ question'''
    f = []
    for q in questions:
        p = re.findall(r'id="(.*?)"', str(q))
        for key in cat_map:
            if key in p[0]:
                f.append((cat_map[key], p[0][-1], q.text))
    f.append(fj)
    return f

def makeadeck(pcv, answer):
    '''Make an Anki deck from the tuples in parse_clue_value()'''
    for i in range(len(pcv)):
        cat = pcv[i][0]
        val = pcv[i][1]
        ques = pcv[i][2]
        ans = answer[i]
        with codecs.open(jeop_cfg['path'] + 'Season' + jeop_cfg['season'] +'.txt', 'a', 'utf-8') as f:
            f.write('{0}~{1}~{2}~{3}\n'.format(cat, val, ques, ans))

def main():
    initial_req = requests.get('http://j-archive.com/showseason.php?season={}'.format(jeop_cfg['season']))
    season_page = initial_req.content
    season_soup = BeautifulSoup(season_page, "html5lib")
    season_game_list = []
    for link in season_soup.findAll("a", attrs={'href': re.compile(r"http://www.j-archive.com/showgame.php")}):
         season_game_list.append(link['href'])
    for game in season_game_list:
        try:
            game_get = requests.get(game)
            game_soup = BeautifulSoup(game_get.content, "html5lib")
            game_cat = game_categories(game_soup)
            questions = game_questions_with_tags(game_soup)
            gqt = game_questions_text(game_soup)
            cat_map = category_map(game_cat)
            answer = answers(game_soup)
            fj = final_jeopardy(gqt, game_cat)
            pcv = parse_clue_value(questions, cat_map, fj)
            makeadeck(pcv, answer)
        except:
            continue

if __name__ == "__main__":
    main()