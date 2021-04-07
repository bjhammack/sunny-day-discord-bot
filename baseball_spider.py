import baseball_spider_variables as bsv
import datetime as dt
import glob
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
from pandas.plotting import table 
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import time
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.utils import ChromeType

class Spider:
	def __init__(self):
		self.today = dt.date.today()
		self.driver = self._prep_driver()
		self.last_homer = ''
		self.team_abbrevs = bsv.team_abbreviations

	def _update_today(self):
		self.today = dt.date.today()
	
	def get_lineups(self, date=None):
		self._update_today()
		if not date:
			date = self.today
		if int(date.month) < 10:
			month = f'0{date.month}'
		else:
			month = date.month
		if int(date.day) < 10:
			day = f'0{date.day}'
		else:
			day = date.day

		url = f'https://www.baseballpress.com/lineups/{date.year}-{month}-{day}'
		self.driver.get(url)
		
		lineups = self.driver.find_elements_by_xpath(f'/html/body/div/div[5]/div/div/div')
		matchups = []
		for lineup in lineups:
			try:
				matchup = {}
				matchup_list = lineup.find_element_by_xpath('div[2]').text.split('\n')[:-2]
				matchup['away'] = matchup_list.pop(0)
				matchup['date'] = matchup_list.pop(0)
				matchup['time'] = matchup_list.pop(0)
				matchup['home'] = matchup_list.pop(0)
				matchup['away_sp'] = matchup_list.pop(0)
				matchup['home_sp'] = matchup_list.pop(0)
				
				if matchup_list[0] == 'No Lineup Released':
					matchup['away_lineup'] = ['','','','','','','','','']
					matchup_list.pop(0)
				else:
					matchup['away_lineup'] = [matchup_list.pop(0) for x in range(9)]

				if matchup_list[0] == 'No Lineup Released':
					matchup['home_lineup'] = ['','','','','','','','','']
					matchup_list.pop(0)
				else:
					matchup['home_lineup'] = [matchup_list.pop(0) for x in range(9)]

				matchups.append(matchup)
			
			except Exception as e:
				pass

		return matchups

	def get_team_lineup(self, team_name):
		matchups = self.get_lineups()

		team = {}
		for i in matchups:
			if self.team_abbrevs[i['away']] == team_name:
				team['team'] = i['away']
				team['date'] = i['date']
				team['time'] = i['time']
				team['sp'] = i['away_sp']
				team['lineup'] = i['away_lineup']
				break
			elif self.team_abbrevs[i['home']] == team_name:
				team['team'] = i['home']
				team['date'] = i['date']
				team['time'] = i['time']
				team['sp'] = i['home_sp']
				team['lineup'] = i['home_lineup']
				break

		return team

	def format_team_lineup(self, team_name=None):
		if not team_name:
			return 'Please enter a valid team name.'
		team = self.get_team_lineup(team_name)
		if len(team) == 0:
			return 'Team does not exist or does not have a lineup for today.'
		else:
			return f'''__**{team['date']}**__
__**{team['time']}**__
__{team['team']}__
*{team['sp']}*
{team['lineup'][0]}
{team['lineup'][1]}
{team['lineup'][2]}
{team['lineup'][3]}
{team['lineup'][4]}
{team['lineup'][5]}
{team['lineup'][6]}
{team['lineup'][7]}
{team['lineup'][8]}
'''

	def get_scores(self, date=None):
		bad_text = bsv.get_scores_bad_text + [v for k,v in self.team_abbrevs.items() if v != 'PIT']
		
		self._update_today()
		if not date:
			date = self.today
		if int(date.month) < 10:
			month = f'0{date.month}'
		else:
			month = date.month
		if int(date.day) < 10:
			day = f'0{date.day}'
		else:
			day = date.day

		url = f'https://www.mlb.com/scores/{date.year}-{month}-{day}'
		self.driver.get(url)

		scores = []
		has_score = True
		score_count = 1
		while has_score == True:
			try:
				new_score = self.driver.find_elements_by_xpath(f'/html/body/main/div[2]/div/section/section[2]/div/div')
				current_score = new_score[0].find_element_by_xpath(f'div[{score_count}]').text
				for bad in bad_text:
					current_score = current_score.replace(bad,'')
				
				current_score = current_score.replace('\n\n','\n').replace('\n\n','\n').replace('\n\n','\n').replace('\n\n','\n')
				
				current_score_list = current_score.split('\n')[:-1]

				matchup_dict = bsv.matchup_dict.copy()
				
				if current_score_list[1] not in list(self.team_abbrevs.keys()):
					matchup_dict['notes'] = current_score_list.pop(1)
				else:
					matchup_dict['notes'] = ''
				abbrvs = list(self.team_abbrevs.values()) + ['SD','SF','TB','CWS']
				[current_score_list.pop(i) for i,j in enumerate(current_score_list) if j in abbrvs]

				if 'TOP' in current_score_list[0] or 'BOT' in current_score_list[0]:
					matchup_dict['state'] = current_score_list[0]
					matchup_dict['home'] = current_score_list[3]
					matchup_dict['away'] = current_score_list[1]
					matchup_dict['home_wl'] = current_score_list[4]
					matchup_dict['away_wl'] = current_score_list[2]
					matchup_dict['rhe'] = current_score_list[5]
					matchup_dict['home_rhe'] = current_score_list[7]
					matchup_dict['away_rhe'] = current_score_list[6]
					matchup_dict['pitcher'] = current_score_list[11]
					matchup_dict['at_bat_text'] = current_score_list[10]
					matchup_dict['pitching_text'] = current_score_list[9]
					matchup_dict['pitcher_stats'] = current_score_list[12]
					matchup_dict['hitter'] = current_score_list[13]
					matchup_dict['hitter_stats'] = current_score_list[14]
					matchup_dict['count'] = current_score_list[8]
				elif 'MID' in current_score_list[0]:
					matchup_dict['state'] = current_score_list[0]
					matchup_dict['home'] = current_score_list[3]
					matchup_dict['away'] = current_score_list[1]
					matchup_dict['home_wl'] = current_score_list[4]
					matchup_dict['away_wl'] = current_score_list[2]
					matchup_dict['rhe'] = current_score_list[5]
					matchup_dict['home_rhe'] = current_score_list[7]
					matchup_dict['away_rhe'] = current_score_list[6]
					matchup_dict['due_1'] = current_score_list[10]
					matchup_dict['due_2'] = current_score_list[12]
					matchup_dict['due_3'] = current_score_list[14]
					matchup_dict['due_1_stats'] = current_score_list[11]
					matchup_dict['due_2_stats'] = current_score_list[13]
					matchup_dict['due_3_stats'] = current_score_list[15]
					matchup_dict['due_text'] = current_score_list[9]
				elif current_score_list[0] == 'FINAL':
					matchup_dict['state'] = current_score_list[0]
					matchup_dict['home'] = current_score_list[3]
					matchup_dict['away'] = current_score_list[1]
					matchup_dict['home_wl'] = current_score_list[4]
					matchup_dict['away_wl'] = current_score_list[2]
					matchup_dict['rhe'] = current_score_list[5]
					matchup_dict['home_rhe'] = current_score_list[7]
					matchup_dict['away_rhe'] = current_score_list[6]
					matchup_dict['w'] = current_score_list[9]
					matchup_dict['w_stats'] = current_score_list[10]
					matchup_dict['l'] = current_score_list[12]
					matchup_dict['l_stats'] = current_score_list[13]
					matchup_dict['w_text'] = current_score_list[8]
					matchup_dict['l_text'] = current_score_list[11]
					try:
						matchup_dict['s_text'] = current_score_list[14]
						matchup_dict['s'] = current_score_list[15]
						matchup_dict['s_count'] = current_score_list[16]
					except:
						matchup_dict['s_text'] = ''
						matchup_dict['s'] = ''
						matchup_dict['s_count'] = ''
				elif current_score_list[0] == 'POSTPONED':
					matchup_dict['state'] = current_score_list[0]
					matchup_dict['home'] = current_score_list[3]
					matchup_dict['away'] = current_score_list[1]
					matchup_dict['home_wl'] = current_score_list[4]
					matchup_dict['away_wl'] = current_score_list[2]
					matchup_dict['home_sp'] = current_score_list[7]
					matchup_dict['away_sp'] = current_score_list[5]
					matchup_dict['home_sp_hand'] = current_score_list[8]
					matchup_dict['away_sp_hand'] = current_score_list[6]
				else:
					matchup_dict['state'] = current_score_list[0]
					matchup_dict['home'] = current_score_list[3]
					matchup_dict['away'] = current_score_list[1]
					matchup_dict['home_wl'] = current_score_list[4]
					matchup_dict['away_wl'] = current_score_list[2]
					matchup_dict['home_sp'] = current_score_list[8]
					matchup_dict['away_sp'] = current_score_list[5]
					matchup_dict['home_sp_hand'] = current_score_list[9]
					matchup_dict['away_sp_hand'] = current_score_list[6]
					matchup_dict['home_sp_stats'] = current_score_list[10]
					matchup_dict['away_sp_stats'] = current_score_list[7]

				scores.append(matchup_dict)
				score_count += 1
			except Exception as e:
				has_score = False

		return scores

	def get_team_score(self, team):
		scores = self.get_scores()
		abbrv = {v:k for k,v in self.team_abbrevs.items()}
		score = ''
		for i in scores:
			if abbrv[team] in i:
				score += i

		return score

	def generate_lineup_images(self):
		self._empty_lineups()
		matchups = self.get_lineups()

		for i,matchup in enumerate(matchups):
			matchup_dict = {
				'Away': ['',matchup['away'],matchup['away_sp']]+matchup['away_lineup'],
				matchup['date']: [matchup['time'],'','','','','','','','','','',''],
				'Home': ['',matchup['home'],matchup['home_sp']]+matchup['home_lineup']
			}
			df = pd.DataFrame(matchup_dict)
			
			fig, ax = self._render_mpl_table(df)

			plt.savefig(f'lineups/lineup{i+1}.png')
			plt.close(fig)

	def generate_score_images(self):
		self._empty_scores()
		matchups = self.get_scores()

		for i,j in enumerate(matchups):
			matchup_dict = {
				'Away': ['',j['away'],j['away_wl'],j['away_sp']+j['rhe'],j['away_rhe']\
					+j['away_sp_hand'],j['away_sp_stats'],j['due_text']+j['w_text']\
					+j['pitching_text'],j['pitcher']+j['due_1']+j['l_text']\
					,j['due_1_stats']+j['s_text']+j['at_bat_text'],j['hitter'],j['count']],
				j['state']: [j['notes'],'@','','','','',j['w']\
					,j['l']+j['due_2']+j['pitcher_stats'],j['s']+j['due_2_stats']\
					,j['hitter_stats'],''],
				'Home': ['',j['home'],j['home_wl'],j['home_sp']+j['rhe'],j['home_rhe']\
					+j['home_sp_hand'],j['home_sp_stats'],j['w_stats']\
					,j['due_3']+j['l_stats']\
					,j['due_3_stats']+j['s_count'],'','']
			}
			
			df = pd.DataFrame(matchup_dict)
			
			fig, ax = self._render_mpl_table(df)

			plt.savefig(f'scores/score{i+1}.png')
			plt.close(fig)

	def generate_team_score_image(self, team):
		self._empty_scores()
		matchups = self.get_scores()
		abbrvs = {v:k for k,v in self.team_abbrevs.items()}
		matchups = [j for i,j in enumerate(matchups) if j['away'] == abbrvs[team] or j['home'] == abbrvs[team]]

		for i,j in enumerate(matchups):
			matchup_dict = {
				'Away': ['',j['away'],j['away_wl'],j['away_sp']+j['rhe'],j['away_rhe']\
					+j['away_sp_hand'],j['away_sp_stats'],j['due_text']+j['w_text']\
					+j['pitching_text'],j['pitcher']+j['due_1']+j['l_text']\
					,j['due_1_stats']+j['s_text']+j['at_bat_text'],j['hitter'],j['count']],
				j['state']: [j['notes'],'@','','','','',j['w']\
					,j['l']+j['due_2']+j['pitcher_stats'],j['s']+j['due_2_stats']\
					,j['hitter_stats'],''],
				'Home': ['',j['home'],j['home_wl'],j['home_sp']+j['rhe'],j['home_rhe']\
					+j['home_sp_hand'],j['home_sp_stats'],j['w_stats']\
					,j['due_3']+j['l_stats']\
					,j['due_3_stats']+j['s_count'],'','']
			}
			
			df = pd.DataFrame(matchup_dict)
			
			fig, ax = self._render_mpl_table(df)

			plt.savefig(f'scores/score{i+1}.png')
			plt.close(fig)

	def get_homers(self):
		self.driver.get('https://twitter.com/DingerTracker')
		time.sleep(5)
		spans = self.driver.find_elements_by_tag_name('span')
		span_text = [i.text for i in spans]
		#homers = [i.text for i in spans if '-' in  i.text and 'Carousel' not in i.text]
		homers = ['\n'.join(i.split('\n')[2:5]) for i in span_text if 'Hit' in i]
		new_homers = []
		for homer in homers:
			if homer != self.last_homer:
				new_homers.append(homer)
			else:
				break

		if len(new_homers) > 0:
			self.last_homer = new_homers[0]
		
		new_homers.reverse()
		return new_homers

	def _render_mpl_table(self, data, col_width=2.5, row_height=0.625, font_size=14,
						header_color='w', row_colors=['w', 'w'], edge_color='w',
						bbox=[0, 0, 1, 1], header_columns=0,
						ax=None, **kwargs):
		if ax is None:
			size = (np.array(data.shape[::-1]) + np.array([0, 1])) * np.array([col_width, row_height])
			fig, ax = plt.subplots(figsize=size)
			ax.axis('off')
		mpl_table = ax.table(cellText=data.values, bbox=bbox, colLabels=data.columns, **kwargs)
		mpl_table.auto_set_font_size(False)
		mpl_table.set_fontsize(font_size)

		for k, cell in mpl_table._cells.items():
			cell.set_edgecolor(edge_color)
		if k[0] == 0 or k[1] < header_columns:
			#cell.set_text_props(weight='bold', color='w')
			#cell.set_facecolor(header_color)
			placeholder = None
		else:
			cell.set_facecolor(row_colors[k[0]%len(row_colors) ])
		
		return ax.get_figure(), ax

	def _empty_lineups(self):
		files = glob.glob('lineups/*')
		for f in files:
			os.remove(f)
	def _empty_scores(self):
		files = glob.glob('scores/*')
		for f in files:
			os.remove(f)

	def _prep_driver(self):
		'''
		Prepare Selenium webdriver for scraping and setting chromedriver arguments

		Returns: selenium driver for webscraping
		'''
		options = webdriver.ChromeOptions()
		#options.add_argument('--ignore-certificate-errors')
		#options.add_argument('--incognito')
		options.add_argument('--headless')
		options.add_argument("--log-level=3")
		options.add_argument("--remote-debugging-port=9222")
		# Deprecated version of creating the driver. This is the preferred approach, but does not work with 32-bit linux OS's
		driver = webdriver.Chrome(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install(),options=options)
		#driver = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver', options=options)
		
		return driver
