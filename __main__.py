import calendar
import csv
import os
import re
import urllib.parse
import sys
import requests

from bs4 import BeautifulSoup as bS
from nameparser import HumanName
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait

from multiprocessing import Pool


max_defendants_count = 0

def search_cases(browser_driver, month, year):
    try:
        fill_panel_details(browser_driver)

        select_tab(browser_driver)

        fill_tab_panel_details(browser_driver, month, year)

        submit_form(browser_driver)

    except Exception as e:
        exception = sys.exc_info()
        print("{0} || LINE - {1} || {2}".format(exception[0], exception[2].tb_lineno, e))
        browser_driver.close()


def fill_panel_details(browser_driver):
    """

    :param browser_driver:
    :return:
    """
    try:
        #  *************** Select Number of results *******************
        num_of_results_select = WebDriverWait(browser_driver, 30).until(
            EC.presence_of_element_located((By.NAME, "pageSize"))
        )
        if num_of_results_select:
            num_of_results_select = Select(browser_driver.find_element_by_name('pageSize'))
            num_of_results_select.select_by_visible_text('75')

        #  *************** Select Court Department *******************
        court_department_select = Select(browser_driver.find_element_by_name('sdeptCd'))
        court_department_select.select_by_visible_text('Land Court Department')

    except Exception as e:
        exception = sys.exc_info()
        print("{0} || LINE - {1} || {2}".format(exception[0], exception[2].tb_lineno, e))
        browser_driver.close()


def select_tab(browser_driver):
    """

    :param browser_driver:
    :return:
    """
    try:
        #  *************** Select Case Type Tab *******************
        case_type_tab = WebDriverWait(browser_driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "tab1"))
        )
        case_type_tab.click()
    except Exception as e:
        exception = sys.exc_info()
        print("{0} || LINE - {1} || {2}".format(exception[0], exception[2].tb_lineno, e))
        browser_driver.close()
        sys.exit()


def fill_tab_panel_details(browser_driver, month, year):
    """

    :param browser_driver:
    :return:
    """
    try:
        start_day, end_day = calendar.monthrange(year, int(month))

        #  *************** Select case type dropdown  *******************
        case_type_element = WebDriverWait(browser_driver, 10).until(
            EC.presence_of_element_located((By.NAME, "caseCd"))
        )
        case_type_select = Select(case_type_element)
        case_type_select.select_by_visible_text("Tax Lien")

        #  *************** Select begin date dropdown  *******************
        begin_date = browser_driver.find_element_by_name("fileDateRange:dateInputBegin")
        begin_date.clear()
        begin_date.send_keys("{month}/{date}/{year}".format(date="01", month=str(month).zfill(2), year=year))

        #  *************** Select end date dropdown  *******************
        end_date = browser_driver.find_element_by_name("fileDateRange:dateInputEnd")
        end_date.clear()
        end_date.send_keys("{month}/{date}/{year}".format(date=str(end_day).zfill(2), month=str(month).zfill(2), year=year))

        #  *************** Select case status dropdown  *******************
        status_select = Select(browser_driver.find_element_by_name('statCd'))
        status_select.deselect_all()
        status_select.select_by_visible_text("Open")

        #  *************** Select party type dropdown  *******************
        party_type_select = Select(browser_driver.find_element_by_name('ptyCd'))
        party_type_select.deselect_all()
        party_type_select.select_by_visible_text("Plaintiff")

        #  *************** Select city/ town dropdown  *******************
        city_select = Select(browser_driver.find_element_by_name('cityCd'))
        city_select.deselect_all()
        city_select.select_by_visible_text("All Cities")

    except Exception as e:
        exception = sys.exc_info()
        print("{0} || LINE - {1} || {2}".format(exception[0], exception[2].tb_lineno, e))
        browser_driver.close()
        sys.exit()


def submit_form(browser_driver):
    """

    :param browser_driver:
    :return:
    """

    try:
        submit_button = browser_driver.find_element_by_name("submitLink")
        submit_button.submit()
    except Exception as e:
        exception = sys.exc_info()
        print("{0} || LINE - {1} || {2}".format(exception[0], exception[2].tb_lineno, e))
        browser_driver.close()
        sys.exit()


def scrape_search_results(browser_driver):
    try:
        address_links = []

        html = browser_driver.page_source

        soup = bS(html, 'html.parser')

        table_body = soup.find('tbody')
        rows = table_body.find_all('tr')

        for row in rows:
            sub_col = row.find_all('td')

            a_tag = sub_col[2].find('a')

            base_url = str(browser_driver.current_url).split("?")[0]

            address_links.append(urllib.parse.urljoin(base_url, a_tag['href']))

        return address_links

    except Exception as e:
        exception = sys.exc_info()
        print("{0} || LINE - {1} || {2}".format(exception[0], exception[2].tb_lineno, e))
        browser_driver.close()
        sys.exit()


def get_next_search_result_page(browser_driver):
    try:
        navigator = browser_driver.find_element_by_class_name("navigator")
        navigator.find_element_by_xpath('//*[@title="Go to next page"]')

    except NoSuchElementException as e:
        print(e)
        pass


def is_defendant_listed(browser_driver, docket_terms):
    try:
        html = browser_driver.page_source
        is_found = False

        for term in docket_terms:
            if re.search(term, html, re.IGNORECASE):
                is_found = True
                break

        return is_found
    except Exception as e:
        exception = sys.exc_info()
        print("{0} || LINE - {1} || {2}".format(exception[0], exception[2].tb_lineno, e))
        browser_driver.close()
        sys.exit()


def _get_docket_date(browser_driver, docket_terms):
    docket_date = ""

    try:
        docket_info = browser_driver.find_element_by_id("docketInfo")
        docket_table = docket_info.find_element_by_class_name("tablesorter")

        tr_tags = docket_table.find_elements_by_tag_name("tr")[1:]

        for tr_tag in tr_tags:
            td_date = tr_tag.find_elements_by_tag_name("td")[0]
            td_info = tr_tag.find_elements_by_tag_name("td")[1]

            for docket_term in docket_terms:
                if docket_term in td_info.text:
                    docket_date = td_date.text
                    break

        return docket_date
    except Exception as e:
        exception = sys.exc_info()
        print("{0} || LINE - {1} || {2}".format(exception[0], exception[2].tb_lineno, e))
        browser_driver.close()
        sys.exit()


def _get_file_date(browser_driver):
    """

    :param browser_driver:
    :return:
    """
    try:
        header = browser_driver.find_element_by_id("caseHeader")
        file_date = header.find_elements_by_class_name("caseHdrInfo")[2]

        return file_date.text
    except Exception as e:
        exception = sys.exc_info()
        print("{0} || LINE - {1} || {2}".format(exception[0], exception[2].tb_lineno, e))
        browser_driver.close()
        sys.exit()


def _get_case_status(browser_driver):
    """

    :param browser_driver:
    :return:
    """
    try:
        header = browser_driver.find_element_by_id("caseHeader")
        case_status = header.find_elements_by_class_name("caseHdrInfo")[1]

        return case_status.text
    except Exception as e:
        exception = sys.exc_info()
        print("{0} || LINE - {1} || {2}".format(exception[0], exception[2].tb_lineno, e))
        browser_driver.close()
        sys.exit()


def get_case_number(browser_driver):
    try:
        tile_bar = browser_driver.find_element_by_id("titleBar")
        display_data = tile_bar.find_element_by_class_name("displayData")

        case_number = " ".join(str(display_data.text).split()[:3])
        return case_number

    except Exception as e:
        exception = sys.exc_info()
        print("{0} || LINE - {1} || {2}".format(exception[0], exception[2].tb_lineno, e))
        browser_driver.close()
        sys.exit()


def get_property_address(browser_driver):
    """

    :param browser_driver:
    :return:
    """
    try:
        address = browser_driver.find_element_by_id("addressInfo")
        city = address.find_elements_by_tag_name("div")[3].text
        street = address.find_elements_by_tag_name("div")[2].text
        zip_code = address.find_elements_by_tag_name("div")[1].text

        full_address = {"zip": zip_code, "street": street, "city": city}
        return full_address

    except Exception as e:
        exception = sys.exc_info()
        print("{0} || LINE - {1} || {2}".format(exception[0], exception[2].tb_lineno, e))
        browser_driver.close()
        sys.exit()


def _get_defendant(party_name):
    """

    :param str party_name:
    :return:
    """

    try:
        if party_name.count(',') > 1:
            party_name = ''.join(party_name.rsplit(',', 1))

        full_name = HumanName(party_name)
        full_name.middle = full_name.middle.replace(".", "")

        return full_name
    except Exception as e:
        exception = sys.exc_info()
        print("{0} || LINE - {1} || {2}".format(exception[0], exception[2].tb_lineno, e))


def _get_defendant_list(browser_driver):
    """

    :param browser_driver:
    :return:
    """
    party_info = []
    party_types = browser_driver.find_elements_by_class_name("ptyType")
    party_names = browser_driver.find_elements_by_class_name("ptyInfoLabel")

    try:
        index = 0
        for party_type in party_types:

            if "Defendant" in party_type.text:

                party_name = party_names[index].text
                defendant = _get_defendant(party_name)

                if defendant.first and defendant.last:
                    party_info.append({"first_name": defendant.first, "last_name": defendant.last,
                                       "middle_name": defendant.middle})
            index += 1

        return party_info
    except Exception as e:
        exception = sys.exc_info()
        print("{0} || LINE - {1} || {2}".format(exception[0], exception[2].tb_lineno, e))
        browser_driver.close()
        sys.exit()


def get_case(browser_driver, terms):
    try:

        full_address = get_property_address(browser_driver=browser_driver)
        file_date = _get_file_date(browser_driver=browser_driver)
        case_status = _get_case_status(browser_driver=browser_driver)
        defendants = _get_defendant_list(browser_driver=browser_driver)
        case_number = get_case_number(browser_driver)
        docket_date = _get_docket_date(browser_driver, terms)

        case_info = {"party": "",
                     "defendants": defendants,
                     "city": full_address['city'],
                     "street": full_address['street'],
                     "zip": full_address['zip'],
                     "file_date": file_date,
                     "case_status": case_status,
                     "docket_date": docket_date,
                     "ma":""}

        case = {"case_number": case_number, "case_info": case_info}

        return case

    except Exception as e:
        exception = sys.exc_info()
        print("{0} || LINE - {1} || {2}".format(exception[0], exception[2].tb_lineno, e))
        browser_driver.close()
        sys.exit()


def _get_defendant_output_lines(defendants, defendant_info_line):
    line = ""

    try:
        for defendant in defendants:
            defendant_line = defendant_info_line.format(**defendant)
            line += defendant_line

        return line
    except Exception as e:
        exception = sys.exc_info()
        print("{0} || LINE - {1} || {2}".format(exception[0], exception[2].tb_lineno, e))


def _get_defendant_header_line(defendant_count, defendant_header):
    defendant_header_line = ""

    try:
        for count in range(1, defendant_count+1):
            defendant_header_line += defendant_header.format(count)

        return defendant_header_line + "\n"
    except Exception as e:
        exception = sys.exc_info()
        print("{0} || LINE - {1} || {2}".format(exception[0], exception[2].tb_lineno, e))


def _get_file_output_lines(case_list):
    global max_defendants_count

    defendant_header = ",Defendant {0} First Name, Defendant {0} Middle Initial, Defendant {0} Last Name"
    defendant_info_line = ",{first_name},{middle_name},{last_name}"
    case_number_line = "{case_number}"
    case_info_line = ",{party},{file_date},{case_status},{docket_date},{city},{street},{zip},{ma}"

    line = ""
    defendant_header_line = ""

    try:
        for case in case_list:
            case_info_dict = case['case_info']

            # ************ Create Case Number line ************
            case_number_output_line = case_number_line.format(**case)

            # ************ Create Case Info line ************
            case_info_output_line = case_info_line.format(**case_info_dict)

            # ************ Create Defendants headers and rows ************
            defendants = case_info_dict['defendants']

            # Get defendant count and store the max count to create header
            defendant_count = len(defendants)
            if defendant_count > max_defendants_count:
                max_defendants_count = defendant_count

            defendant_output_lines = _get_defendant_output_lines(defendants, defendant_info_line)

            # ************ Concatenate lines ************
            line += case_number_output_line + case_info_output_line + defendant_output_lines + "\n"

        defendant_header_line = _get_defendant_header_line(max_defendants_count, defendant_header)
        return line, defendant_header_line

    except Exception as e:
        exception = sys.exc_info()
        print("{0} || LINE - {1} || {2}".format(exception[0], exception[2].tb_lineno, e))


def write_csv(case_list, year):

    base_header_line = "CASE NUMBER,Party/Company,File Date,Case Status,Docket Date," \
                       "City/Case Property,Street/Case Property,Zipcode/Case Property,MA/Case Property"
    file_name = "TaxFile_{0}.csv".format(year)

    try:
        exists = os.path.isfile(file_name)

        with open(file_name, 'a', newline='') as csvfile:

            # writer = csv.writer(csvfile, delimiter=',')

            #  Write blank line for header.
            if not exists:
                # writer.writerow("")
                csvfile.write("\n")

            line, defendant_header_line = _get_file_output_lines(case_list)
            # writer.writerows(line)
            csvfile.write(line)

        # ************ Write headers ************
        with open(file_name, 'r') as file:
            new_lines = file.readlines()
            new_lines[0] = base_header_line + defendant_header_line

        with open(file_name, 'w') as file:
            file.writelines(new_lines)
    except Exception as e:
        exception = sys.exc_info()
        print("{0} || LINE - {1} || {2}".format(exception[0], exception[2].tb_lineno, e))


def click_captcha_checkbox(browser_driver, check, site):
    try:
        if not check:
            browser_driver.get(site)
            mainWin = browser_driver.current_window_handle

            elem = WebDriverWait(browser_driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "iframe"))
            )

            if elem:
                browser_driver.switch_to.frame(browser_driver.find_elements_by_tag_name("iframe")[0])
                CheckBox = WebDriverWait(browser_driver, 10).until(
                    EC.presence_of_element_located((By.ID, "recaptcha-anchor"))
                )
                CheckBox.click()
                browser_driver.switch_to.window(mainWin)

    except Exception as e:
        exception = sys.exc_info()
        print("{0} || LINE - {1} || {2}".format(exception[0], exception[2].tb_lineno, e))
        browser_driver.close()
        sys.exit()


def click_captcha_button(browser_driver, site):
    try:
        browser_driver.get(site)

        button = WebDriverWait(browser_driver, 10).until(
            EC.presence_of_element_located((By.ID, "acknowledgement"))
        )
        a_tag = button.find_element_by_tag_name("a")
        a_tag.click()
    except Exception as e:
        exception = sys.exc_info()
        print("{0} || LINE - {1} || {2}".format(exception[0], exception[2].tb_lineno, e))
        browser_driver.close()
        sys.exit()


def scroll_through_case_listing(case_links, browser_driver):
    is_last_page = False

    while not is_last_page:

        try:
            navigator = browser_driver.find_element_by_class_name("navigator")
            button = navigator.find_element_by_xpath('//*[@title="Go to next page"]')
            href_data = button.get_attribute('href')

            if href_data:
                button.click()
                new_address_links = scrape_search_results(browser_driver=browser_driver)
                case_links.extend(new_address_links)
            else:
                is_last_page = True

        except NoSuchElementException:
            is_last_page = True


def crawl_site(year, site, browser_driver):

    browser_driver.get(site)

    is_first = True

    terms = ['Motion for General Default', 'Motion for Judgment Allowed', 'Motion for Judgement Allowed',
             'Motion for Judgment Default', 'Motion for Judgement Default', 'Motion for Judgment',
             'Motion for Judgement', 'Motion for General']

    print('Press "Return" AFTER solving CAPTCHA')
    x = input()
    print('Resume scrapping .. ')

    cases = []
    for month in range(1, 13):

        # **************** Checks captcha after first solve  ****************
        if not is_first:
            click_captcha_button(browser_driver, site)

        # **************** Search for defendants ****************
        search_cases(browser_driver=browser_driver, month=month, year=year)

        # **************** Search for case links ****************
        case_links = scrape_search_results(browser_driver=browser_driver)

        #  Go through pages
        scroll_through_case_listing(case_links, browser_driver)

        for address_link in case_links:
            browser_driver.get(address_link)

            is_listed = is_defendant_listed(browser_driver, terms)
            if is_listed:
                case = get_case(browser_driver=browser_driver, terms=terms)
                print(len(case))
                cases.append(case)

        is_first = False

    write_csv(cases, year)

    browser_driver.close()


if __name__ == '__main__':

    year = int(sys.argv[1])
    site = str(sys.argv[2])
    browser_driver = str(sys.argv[3])


    try:
        crawl_site(year, site, browser_driver)

    except Exception as e:
        exception = sys.exc_info()
        print("{0} || LINE - {1} || {2}".format(exception[0], exception[2].tb_lineno, e))
        sys.exit()
